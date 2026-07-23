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

readonly TEMPLATE_TOOLS_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TEMPLATE_TOOLS_TEMP_DIR=""

cleanup() {
    if [[ -n "$TEMPLATE_TOOLS_TEMP_DIR" && -d "$TEMPLATE_TOOLS_TEMP_DIR" ]]; then
        rm -rf "$TEMPLATE_TOOLS_TEMP_DIR"
    fi
}
trap cleanup EXIT

fail() {
    printf 'error: %s\n' "$*" >&2
    exit 1
}

assert_file() {
    local file_path="$1"
    [[ -f "$file_path" ]] || fail "expected generated file: $file_path"
}

assert_directory() {
    local directory_path="$1"
    [[ -d "$directory_path" ]] || fail "expected generated directory: $directory_path"
}

assert_contains() {
    local file_path="$1"
    local expected="$2"
    grep -Fq -- "$expected" "$file_path" \
        || fail "expected '$expected' in $file_path"
}

assert_occurrences() {
    local file_path="$1"
    local expected="$2"
    local expected_count="$3"
    local actual_count

    actual_count="$(grep -Fc -- "$expected" "$file_path" || true)"
    [[ "$actual_count" == "$expected_count" ]] \
        || fail "expected $expected_count occurrence(s) of '$expected' in $file_path; found $actual_count"
}

check_rename_dry_run() {
    local status_before
    local status_after
    local output

    status_before="$(git status --porcelain=v1 --untracked-files=all)"
    output="$(
        bash "$TEMPLATE_TOOLS_ROOT/scripts/rename-template.sh" \
            --package com.example.verification \
            --name "Verification App" \
            --plugin-alias verification \
            --dry-run \
            --force \
            2>&1
    )"
    status_after="$(git status --porcelain=v1 --untracked-files=all)"

    [[ "$status_before" == "$status_after" ]] \
        || fail "rename-template.sh --dry-run changed the working tree"
    grep -Fq -- "DRY RUN" <<<"$output" \
        || fail "rename dry run did not report dry-run mode"
    grep -Fq -- "feature/home/" <<<"$output" \
        || fail "rename dry run did not inspect the reference feature"
}

check_generated_module_structure() {
    local fixture_root

    TEMPLATE_TOOLS_TEMP_DIR="$(
        mktemp -d "${TMPDIR:-/tmp}/compose-template-tools.XXXXXX"
    )"
    fixture_root="$TEMPLATE_TOOLS_TEMP_DIR/repository"

    mkdir -p "$fixture_root/scripts"
    cp "$TEMPLATE_TOOLS_ROOT/scripts/add-module.sh" "$fixture_root/scripts/add-module.sh"
    cp "$TEMPLATE_TOOLS_ROOT/settings.gradle.kts" "$fixture_root/settings.gradle.kts"

    (
        cd "$fixture_root"
        bash scripts/add-module.sh \
            --type android \
            --name modulecheck \
            --parent feature \
            --package app.template.feature.modulecheck
        bash scripts/add-module.sh \
            --type kotlin \
            --name logiccheck \
            --parent core \
            --package app.template.core.logiccheck
    )

    assert_file "$fixture_root/feature/modulecheck/build.gradle.kts"
    assert_file "$fixture_root/feature/modulecheck/consumer-rules.pro"
    assert_file "$fixture_root/feature/modulecheck/proguard-rules.pro"
    assert_file "$fixture_root/feature/modulecheck/src/main/AndroidManifest.xml"
    assert_directory "$fixture_root/feature/modulecheck/src/androidTest/kotlin"
    assert_file \
        "$fixture_root/feature/modulecheck/src/main/kotlin/app/template/feature/modulecheck/Modulecheck.kt"
    assert_file \
        "$fixture_root/feature/modulecheck/src/test/kotlin/app/template/feature/modulecheck/ModulecheckTest.kt"
    assert_contains \
        "$fixture_root/feature/modulecheck/build.gradle.kts" \
        "alias(libs.plugins.androidlab.android.feature)"
    assert_contains \
        "$fixture_root/feature/modulecheck/build.gradle.kts" \
        'namespace = "app.template.feature.modulecheck"'

    assert_file "$fixture_root/core/logiccheck/build.gradle.kts"
    assert_file \
        "$fixture_root/core/logiccheck/src/main/kotlin/app/template/core/logiccheck/Logiccheck.kt"
    assert_file \
        "$fixture_root/core/logiccheck/src/test/kotlin/app/template/core/logiccheck/LogiccheckTest.kt"
    assert_contains \
        "$fixture_root/core/logiccheck/build.gradle.kts" \
        "alias(libs.plugins.androidlab.jvm.library)"

    assert_occurrences \
        "$fixture_root/settings.gradle.kts" \
        'include(":feature:modulecheck")' \
        1
    assert_occurrences \
        "$fixture_root/settings.gradle.kts" \
        'include(":core:logiccheck")' \
        1
}

cd "$TEMPLATE_TOOLS_ROOT"
check_rename_dry_run
check_generated_module_structure
printf 'Template tool checks passed.\n'
