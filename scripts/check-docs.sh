#!/usr/bin/env bash
#
# Designed and developed by 2026 ashtanko (Oleksii Shtanko)
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

set -euo pipefail

readonly REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

failures=0

fail() {
    printf 'error: %s\n' "$*" >&2
    failures=$((failures + 1))
}

check_canonical_agent_entrypoint() {
    if ! rg --quiet --line-regexp '@AGENTS\.md' CLAUDE.md; then
        fail "CLAUDE.md must import the canonical AGENTS.md entrypoint"
    fi
}

check_local_markdown_links() {
    local markdown_file
    local markdown_dir
    local raw_target
    local target

    while IFS= read -r markdown_file; do
        markdown_dir="$(dirname "$markdown_file")"

        while IFS= read -r raw_target; do
            target="${raw_target#<}"
            target="${target%>}"

            case "$target" in
                "" | \#* | http://* | https://* | mailto:* | tel:* | app://*)
                    continue
                    ;;
            esac

            target="${target%%#*}"
            target="${target%%\?*}"

            if [[ -n "$target" && "$target" != /* && ! -e "$markdown_dir/$target" ]]; then
                fail "$markdown_file links to missing path: $raw_target"
            fi
        done < <(
            perl -ne 'while (/\[[^\]]+\]\(([^)]+)\)/g) { print "$1\n" }' "$markdown_file"
        )
    done < <(rg --files --glob '*.md' --glob '!**/build/**' | sort)
}

check_documented_make_targets() {
    local target

    while IFS= read -r target; do
        if ! make --dry-run "$target" >/dev/null; then
            fail "documentation references missing Make target: $target"
        fi
    done < <(
        rg --only-matching --no-filename --pcre2 \
            '(?<=`)make [a-z][a-z0-9-]*(?=`)|^make [a-z][a-z0-9-]*' \
            README.md AGENTS.md .agents \
            | awk '{ print $2 }' \
            | sort --unique
    )
}

check_documented_modules() {
    local module
    local module_path
    local documentation_token

    while IFS= read -r module; do
        module_path="${module//:/\/}"

        if [[ ! -d "$module_path" ]]; then
            fail "settings.gradle.kts includes missing module directory: $module_path"
            continue
        fi

        documentation_token="$module_path"
        if [[ "$module_path" == feature/* ]]; then
            documentation_token="feature/*"
        fi

        if ! rg --fixed-strings --quiet \
            "\`$documentation_token\`" \
            .agents/reference/architecture.md; then
            fail "architecture reference does not cover module: $module_path"
        fi
    done < <(
        sed -nE \
            's/^[[:space:]]*include\(":(.*)"\)[[:space:]]*$/\1/p' \
            settings.gradle.kts
    )
}

check_version_policy() {
    local pinned_version_pattern
    local matches
    local catalog_jdk
    local workflow_jdk
    local documentation_file

    pinned_version_pattern='Android Gradle Plugin[[:space:]]+[0-9]|AGP[[:space:]]+[0-9]|Compose BOM[^[:cntrl:]]*[0-9]{4}\.|Navigation 3[^[:cntrl:]]*\([`*]?[0-9]|Hilt[[:space:]]+[0-9]|(compileSdk|targetSdk|minSdk)[^[:cntrl:]]*[0-9]'

    if matches="$(rg --line-number "$pinned_version_pattern" README.md AGENTS.md .agents)"; then
        printf '%s\n' "$matches" >&2
        fail "mutable dependency and SDK versions belong in gradle/libs.versions.toml, not documentation"
    fi

    catalog_jdk="$(
        sed -nE 's/^jvmTarget[[:space:]]*=[[:space:]]*"([^"]+)"/\1/p' \
            gradle/libs.versions.toml
    )"
    workflow_jdk="$(
        sed -nE \
            "s/^[[:space:]]*JAVA_VERSION:[[:space:]]*['\"]?([0-9]+)['\"]?[[:space:]]*$/\1/p" \
            .github/workflows/ci.yml \
            | head -n 1
    )"

    if [[ -z "$catalog_jdk" ]]; then
        fail "could not read jvmTarget from gradle/libs.versions.toml"
    elif [[ "$workflow_jdk" != "$catalog_jdk" ]]; then
        fail "CI JDK $workflow_jdk does not match version catalog JDK $catalog_jdk"
    fi

    for documentation_file in AGENTS.md README.md .agents/reference/commands.md; do
        if [[ -n "$catalog_jdk" ]] \
            && ! rg --fixed-strings --quiet "JDK $catalog_jdk" "$documentation_file"; then
            fail "$documentation_file must state the configured JDK $catalog_jdk requirement"
        fi
    done
}

check_verification_contract() {
    local verify_recipe
    local required_task

    if ! rg --fixed-strings --quiet "run: make verify" .github/workflows/ci.yml; then
        fail "CI host verification must invoke the canonical make verify target"
    fi

    if rg --quiet \
        'dependencyGuardBaseline|update[A-Za-z]+ScreenshotTest|recordRoborazzi|git-auto-commit-action' \
        .github/workflows/ci.yml; then
        fail "CI verification must not update or commit dependency or screenshot baselines"
    fi

    if rg --quiet 'contents: write|pull-requests: write' .github/workflows/ci.yml; then
        fail "CI verification must not receive broad repository write permissions"
    fi

    verify_recipe="$(
        awk '
            /^verify:/ { in_verify = 1; next }
            in_verify && /^[[:alnum:]_-]+:/ { exit }
            in_verify { print }
        ' Makefile
    )"

    for required_task in \
        assembleDebug \
        test \
        lint \
        detekt \
        spotlessCheck \
        dependencyGuard \
        validateDebugScreenshotTest \
        verifyRoborazziDebug; do
        if ! grep -Fq -- "$required_task" <<<"$verify_recipe"; then
            fail "make verify must include $required_task"
        fi
    done

    if grep -Eq \
        'Baseline|update[A-Za-z]+ScreenshotTest|recordRoborazzi' \
        <<<"$verify_recipe"; then
        fail "make verify must not contain baseline-update tasks"
    fi
}

check_pull_request_maintenance_contract() {
    local required_prompt

    for required_prompt in \
        "module boundaries or public APIs" \
        "which tests were selected and why" \
        "Screenshot, dependency, lint, or baseline-profile changes are intentional" \
        "security, privacy, performance, documentation, and agent-guidance impacts" \
        "architectural decision record"; do
        if ! rg --fixed-strings --ignore-case --quiet \
            "$required_prompt" \
            .github/PULL_REQUEST_TEMPLATE; then
            fail "pull-request template is missing maintenance prompt: $required_prompt"
        fi
    done

    if ! rg --fixed-strings --ignore-case --quiet \
        "At least once per calendar quarter" \
        .agents/README.md; then
        fail "agent guidance must define a quarterly maintenance audit"
    fi
}

check_canonical_agent_entrypoint
check_local_markdown_links
check_documented_make_targets
check_documented_modules
check_version_policy
check_verification_contract
check_pull_request_maintenance_contract

if ((failures > 0)); then
    printf 'Documentation checks failed with %d error(s).\n' "$failures" >&2
    exit 1
fi

printf 'Documentation checks passed.\n'
