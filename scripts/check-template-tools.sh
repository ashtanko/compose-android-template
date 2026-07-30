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
readonly TEMPLATE_IDENTITY="$TEMPLATE_TOOLS_ROOT/scripts/template-identity.json"
readonly RENAMED_PACKAGE="com.example.verification"
readonly RENAMED_PACKAGE_PATH="com/example/verification"
readonly RENAMED_BUILD_LOGIC_PACKAGE="${RENAMED_PACKAGE}.buildlogic"
readonly RENAMED_BUILD_LOGIC_PATH="${RENAMED_PACKAGE_PATH}/buildlogic"
readonly RENAMED_PLUGIN_ALIAS="verification"
readonly RENAMED_NAME='Research & Development "Lab" $5 <Beta>'
readonly RENAMED_KOTLIN_NAME='Research & Development \"Lab\" \$5 <Beta>'
readonly RENAMED_XML_NAME='Research &amp; Development &quot;Lab&quot; $5 &lt;Beta&gt;'
readonly RENAMED_AUTHOR="Example & Co"
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

assert_not_contains() {
    local file_path="$1"
    local unexpected="$2"
    if grep -Fq -- "$unexpected" "$file_path"; then
        fail "did not expect '$unexpected' in $file_path"
    fi
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

identity_value() {
    local key="$1"

    python3 - "$TEMPLATE_IDENTITY" "$key" <<'PY'
import json
import sys

with open(sys.argv[1], encoding="utf-8") as stream:
    print(json.load(stream)[sys.argv[2]])
PY
}

copy_repository_fixture() {
    local fixture_root="$1"
    local relative_path

    while IFS= read -r -d '' relative_path; do
        [[ -e "$TEMPLATE_TOOLS_ROOT/$relative_path" ]] || continue
        mkdir -p "$fixture_root/$(dirname "$relative_path")"
        cp -Pp "$TEMPLATE_TOOLS_ROOT/$relative_path" "$fixture_root/$relative_path"
    done < <(
        git -C "$TEMPLATE_TOOLS_ROOT" \
            ls-files -z --cached --others --exclude-standard
    )
}

tree_digest() {
    local directory="$1"

    python3 - "$directory" <<'PY'
import hashlib
import os
import pathlib
import sys

root = pathlib.Path(sys.argv[1])
digest = hashlib.sha256()
for path in sorted(item for item in root.rglob("*") if item.is_file()):
    relative = path.relative_to(root)
    digest.update(os.fsencode(relative))
    digest.update(path.read_bytes())
print(digest.hexdigest())
PY
}

assert_tree_not_contains() {
    local directory="$1"
    local unexpected="$2"

    python3 - "$directory" "$unexpected" <<'PY' \
        || fail "found stale template value '$unexpected'"
import pathlib
import sys

root = pathlib.Path(sys.argv[1])
unexpected = sys.argv[2]
for path in sorted(item for item in root.rglob("*") if item.is_file()):
    if any(part in {".gradle", ".kotlin", "build"} for part in path.parts):
        continue
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        continue
    if unexpected in text:
        print(f"stale value in {path}", file=sys.stderr)
        raise SystemExit(1)
PY
}

assert_xml_is_valid() {
    python3 - "$@" <<'PY'
import sys
import xml.etree.ElementTree as element_tree

for path in sys.argv[1:]:
    element_tree.parse(path)
PY
}

assert_old_source_paths_removed() {
    local fixture_root="$1"
    shift

    python3 - "$fixture_root" "$@" <<'PY' \
        || fail "old package directory remains under a source set"
import pathlib
import sys

root = pathlib.Path(sys.argv[1])
old_paths = [tuple(value.split("/")) for value in sys.argv[2:]]
for path in root.rglob("*"):
    if not path.is_dir():
        continue
    relative_parts = path.relative_to(root).parts
    try:
        source_index = relative_parts.index("src")
    except ValueError:
        continue
    if (
        len(relative_parts) <= source_index + 2
        or relative_parts[source_index + 2] not in {"java", "kotlin", "reference"}
    ):
        continue
    for old_path in old_paths:
        if len(relative_parts) >= len(old_path) and relative_parts[-len(old_path):] == old_path:
            print(f"stale source directory: {path}", file=sys.stderr)
            raise SystemExit(1)
PY
}

check_rename_end_to_end() {
    local fixture_root="$1"
    local old_application_package="$2"
    local old_code_package="$3"
    local old_build_logic_package="$4"
    local old_plugin_alias="$5"
    local old_project_name="$6"
    local old_display_name="$7"
    local old_author="$8"
    local digest_before
    local digest_after
    local dry_run_output

    digest_before="$(tree_digest "$fixture_root")"
    dry_run_output="$(
        (
            cd "$fixture_root"
            bash scripts/rename-template.sh \
                --package "$RENAMED_PACKAGE" \
                --name "$RENAMED_NAME" \
                --plugin-alias "$RENAMED_PLUGIN_ALIAS" \
                --author "$RENAMED_AUTHOR" \
                --dry-run \
                --verbose \
                --force
        ) 2>&1
    )"
    digest_after="$(tree_digest "$fixture_root")"

    [[ "$digest_before" == "$digest_after" ]] \
        || fail "rename-template.sh --dry-run changed the fixture"
    grep -Fq -- "DRY RUN" <<<"$dry_run_output" \
        || fail "rename dry run did not report dry-run mode"
    grep -Fq -- "feature/home/" <<<"$dry_run_output" \
        || fail "rename dry run did not inspect feature source paths"
    grep -Fq -- "build-logic/convention/src/test/" <<<"$dry_run_output" \
        || fail "rename dry run did not inspect build-logic test paths"

    (
        cd "$fixture_root"
        bash scripts/rename-template.sh \
            --package "$RENAMED_PACKAGE" \
            --name "$RENAMED_NAME" \
            --plugin-alias "$RENAMED_PLUGIN_ALIAS" \
            --author "$RENAMED_AUTHOR" \
            --force >/dev/null
    )

    assert_file "$fixture_root/app/src/main/kotlin/$RENAMED_PACKAGE_PATH/App.kt"
    assert_file \
        "$fixture_root/core/navigation/src/test/kotlin/$RENAMED_PACKAGE_PATH/core/navigation/NavigatorTest.kt"
    assert_file \
        "$fixture_root/feature/home/src/screenshotTest/kotlin/$RENAMED_PACKAGE_PATH/feature/home/HomeScreenScreenshotTest.kt"
    assert_file \
        "$fixture_root/build-logic/convention/src/test/kotlin/$RENAMED_BUILD_LOGIC_PATH/detekt/ExplicitVisibilityRuleTest.kt"
    assert_file \
        "$fixture_root/benchmarks/src/main/java/$RENAMED_PACKAGE_PATH/benchmarks/BaselineProfileGenerator.kt"

    assert_contains \
        "$fixture_root/settings.gradle.kts" \
        "rootProject.name = \"$RENAMED_KOTLIN_NAME\""
    assert_contains \
        "$fixture_root/app/src/main/res/values/strings.xml" \
        "<string name=\"app_name\" translatable=\"false\">$RENAMED_XML_NAME</string>"
    assert_contains \
        "$fixture_root/feature/home/src/main/res/values/strings.xml" \
        "<string name=\"feature_home_title\" translatable=\"false\">$RENAMED_XML_NAME</string>"
    assert_contains \
        "$fixture_root/app/src/androidTest/kotlin/$RENAMED_PACKAGE_PATH/MainNavigationTest.kt" \
        "onNodeWithText(\"$RENAMED_KOTLIN_NAME\")"
    assert_contains \
        "$fixture_root/build-logic/convention/src/main/resources/META-INF/services/io.gitlab.arturbosch.detekt.api.RuleSetProvider" \
        "$RENAMED_BUILD_LOGIC_PACKAGE.detekt.ExplicitVisibilityRuleSetProvider"
    assert_contains \
        "$fixture_root/gradle/libs.versions.toml" \
        "$RENAMED_PLUGIN_ALIAS-android-feature = { id = \"$RENAMED_PLUGIN_ALIAS.android.feature\""
    assert_contains \
        "$fixture_root/feature/home/build.gradle.kts" \
        "alias(libs.plugins.$RENAMED_PLUGIN_ALIAS.android.feature)"
    assert_contains \
        "$fixture_root/scripts/add-module.sh" \
        "PACKAGE=\"$RENAMED_PACKAGE."
    assert_contains \
        "$fixture_root/scripts/check-docs.sh" \
        "Designed and developed by 2026 $RENAMED_AUTHOR"

    assert_xml_is_valid \
        "$fixture_root/app/src/main/res/values/strings.xml" \
        "$fixture_root/feature/home/src/main/res/values/strings.xml"

    assert_old_source_paths_removed \
        "$fixture_root" \
        "${old_application_package//./\/}" \
        "${old_code_package//./\/}" \
        "${old_build_logic_package//./\/}"

    for stale_value in \
        "$old_application_package" \
        "$old_code_package" \
        "$old_build_logic_package" \
        "$old_plugin_alias.android" \
        "$old_plugin_alias.jvm" \
        "$old_plugin_alias.hilt" \
        "$old_plugin_alias.kotlin" \
        "$old_plugin_alias.spotless" \
        "$old_plugin_alias-" \
        "libs.plugins.$old_plugin_alias" \
        "$old_project_name" \
        "$old_display_name" \
        "$old_author"; do
        assert_tree_not_contains "$fixture_root" "$stale_value"
    done

    bash -n \
        "$fixture_root/scripts/rename-template.sh" \
        "$fixture_root/scripts/add-module.sh" \
        "$fixture_root/scripts/check-template-tools.sh"
    python3 -m py_compile "$fixture_root/scripts/rename-template.py"

    (
        cd "$fixture_root"
        bash scripts/rename-template.sh \
            --package com.example.second \
            --name "Second Project" \
            --plugin-alias second \
            --dry-run \
            --force >/dev/null
    )
}

check_renamed_module_generation() {
    local fixture_root="$1"

    (
        cd "$fixture_root"
        printf '\n' | bash scripts/add-module.sh \
            --type android \
            --name modulecheck \
            --parent feature
        printf '\n' | bash scripts/add-module.sh \
            --type android \
            --name androidcheck \
            --parent core
        printf '\n' | bash scripts/add-module.sh \
            --type kotlin \
            --name logiccheck \
            --parent core
    )

    assert_file "$fixture_root/feature/modulecheck/build.gradle.kts"
    assert_file "$fixture_root/feature/modulecheck/consumer-rules.pro"
    assert_file "$fixture_root/feature/modulecheck/proguard-rules.pro"
    assert_file "$fixture_root/feature/modulecheck/src/main/AndroidManifest.xml"
    assert_directory "$fixture_root/feature/modulecheck/src/androidTest/kotlin"
    assert_file \
        "$fixture_root/feature/modulecheck/src/main/kotlin/$RENAMED_PACKAGE_PATH/feature/modulecheck/Modulecheck.kt"
    assert_file \
        "$fixture_root/feature/modulecheck/src/test/kotlin/$RENAMED_PACKAGE_PATH/feature/modulecheck/ModulecheckTest.kt"
    assert_contains \
        "$fixture_root/feature/modulecheck/build.gradle.kts" \
        "alias(libs.plugins.$RENAMED_PLUGIN_ALIAS.android.feature)"
    assert_contains \
        "$fixture_root/feature/modulecheck/build.gradle.kts" \
        "namespace = \"$RENAMED_PACKAGE.feature.modulecheck\""
    assert_not_contains \
        "$fixture_root/feature/modulecheck/build.gradle.kts" \
        "dependencies {"

    assert_file "$fixture_root/core/androidcheck/build.gradle.kts"
    assert_file "$fixture_root/core/androidcheck/consumer-rules.pro"
    assert_file "$fixture_root/core/androidcheck/proguard-rules.pro"
    assert_file "$fixture_root/core/androidcheck/src/main/AndroidManifest.xml"
    assert_directory "$fixture_root/core/androidcheck/src/androidTest/kotlin"
    assert_file \
        "$fixture_root/core/androidcheck/src/main/kotlin/$RENAMED_PACKAGE_PATH/core/androidcheck/Androidcheck.kt"
    assert_file \
        "$fixture_root/core/androidcheck/src/test/kotlin/$RENAMED_PACKAGE_PATH/core/androidcheck/AndroidcheckTest.kt"
    assert_contains \
        "$fixture_root/core/androidcheck/build.gradle.kts" \
        "alias(libs.plugins.$RENAMED_PLUGIN_ALIAS.android.library.compose)"
    assert_contains \
        "$fixture_root/core/androidcheck/build.gradle.kts" \
        "namespace = \"$RENAMED_PACKAGE.core.androidcheck\""
    assert_not_contains \
        "$fixture_root/core/androidcheck/build.gradle.kts" \
        "dependencies {"

    assert_file "$fixture_root/core/logiccheck/build.gradle.kts"
    assert_file \
        "$fixture_root/core/logiccheck/src/main/kotlin/$RENAMED_PACKAGE_PATH/core/logiccheck/Logiccheck.kt"
    assert_file \
        "$fixture_root/core/logiccheck/src/test/kotlin/$RENAMED_PACKAGE_PATH/core/logiccheck/LogiccheckTest.kt"
    assert_contains \
        "$fixture_root/core/logiccheck/build.gradle.kts" \
        "alias(libs.plugins.$RENAMED_PLUGIN_ALIAS.jvm.library)"

    assert_occurrences \
        "$fixture_root/settings.gradle.kts" \
        'include(":feature:modulecheck")' \
        1
    assert_occurrences \
        "$fixture_root/settings.gradle.kts" \
        'include(":core:androidcheck")' \
        1
    assert_occurrences \
        "$fixture_root/settings.gradle.kts" \
        'include(":core:logiccheck")' \
        1
}

check_invalid_inputs() {
    if bash "$TEMPLATE_TOOLS_ROOT/scripts/rename-template.sh" \
        --package com.example.invalid \
        --name Invalid \
        --plugin-alias my-app \
        --dry-run \
        --force >/dev/null 2>&1; then
        fail "rename accepted an invalid plugin alias"
    fi

    if bash "$TEMPLATE_TOOLS_ROOT/scripts/rename-template.sh" \
        --package com.example.when \
        --name Invalid \
        --dry-run \
        --force >/dev/null 2>&1; then
        fail "rename accepted a package containing a reserved keyword"
    fi
}

check_collision_preflight() {
    local fixture_root="$1"
    local collision_file
    local digest_before
    local digest_after

    collision_file="$fixture_root/app/src/main/kotlin/com/example/collision/App.kt"
    mkdir -p "$(dirname "$collision_file")"
    printf 'collision\n' >"$collision_file"
    digest_before="$(tree_digest "$fixture_root")"

    if (
        cd "$fixture_root"
        bash scripts/rename-template.sh \
            --package com.example.collision \
            --name Collision \
            --plugin-alias collision \
            --force >/dev/null 2>&1
    ); then
        fail "rename accepted an existing destination file"
    fi

    digest_after="$(tree_digest "$fixture_root")"
    [[ "$digest_before" == "$digest_after" ]] \
        || fail "collision preflight modified the fixture"
    rm "$collision_file"
    rmdir "$fixture_root/app/src/main/kotlin/com/example/collision"
    rmdir "$fixture_root/app/src/main/kotlin/com/example" 2>/dev/null || true
    rmdir "$fixture_root/app/src/main/kotlin/com" 2>/dev/null || true
}

old_application_package="$(identity_value applicationPackage)"
old_code_package="$(identity_value codePackage)"
old_build_logic_package="$(identity_value buildLogicPackage)"
old_plugin_alias="$(identity_value pluginAlias)"
old_project_name="$(identity_value projectName)"
old_display_name="$(identity_value displayName)"
old_author="$(identity_value author)"

TEMPLATE_TOOLS_TEMP_DIR="$(
    mktemp -d "${TMPDIR:-/tmp}/compose-template-tools.XXXXXX"
)"
fixture_root="$TEMPLATE_TOOLS_TEMP_DIR/repository"
mkdir -p "$fixture_root"
copy_repository_fixture "$fixture_root"

check_invalid_inputs
check_collision_preflight "$fixture_root"
check_rename_end_to_end \
    "$fixture_root" \
    "$old_application_package" \
    "$old_code_package" \
    "$old_build_logic_package" \
    "$old_plugin_alias" \
    "$old_project_name" \
    "$old_display_name" \
    "$old_author"
check_renamed_module_generation "$fixture_root"
printf 'Template tool checks passed.\n'
