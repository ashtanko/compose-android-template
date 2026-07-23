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

# add-module.sh — add a new feature or library module to this project.
#
# Usage:
#   scripts/add-module.sh \
#     --type    [android|kotlin] \
#     --name    "my-module" \
#     --parent  "feature" \
#     --package "app.template.feature.mymodule"
#
# If run without flags, it will prompt you interactively.

set -euo pipefail

# ------------------------------ helpers ---------------------------------------

die()  { printf '\033[31merror:\033[0m %s\n' "$*" >&2; exit 1; }
info() { printf '\033[36m==>\033[0m %s\n' "$*"; }
note() { printf '    %s\n' "$*"; }
warn() { printf '\033[33mwarn:\033[0m %s\n' "$*" >&2; }

# ------------------------------ environment -----------------------------------

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

# ------------------------------ arguments -------------------------------------

TYPE=""
NAME=""
PARENT=""
PACKAGE=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --type)    TYPE="$2"; shift 2 ;;
    --name)    NAME="$2"; shift 2 ;;
    --parent)  PARENT="$2"; shift 2 ;;
    --package) PACKAGE="$2"; shift 2 ;;
    -h|--help)
      sed -n '17,26p' "$0" | sed 's/^# \{0,1\}//'
      exit 0 ;;
    *) die "unknown flag: $1 (try --help)" ;;
  esac
done

# ------------------------------ interactive prompts ---------------------------

if [[ -z "$TYPE" ]]; then
  echo "Select module type:"
  echo "  1) Android Library Module (Jetpack Compose, Android APIs)"
  echo "  2) Kotlin/JVM Library Module (pure Kotlin, no Android APIs)"
  read -rp "Choice [1-2]: " type_choice
  case "$type_choice" in
    1) TYPE="android" ;;
    2) TYPE="kotlin" ;;
    *) die "Invalid choice" ;;
  esac
fi

if [[ -z "$PARENT" ]]; then
  echo "Select target directory (parent):"
  echo "  1) feature/ (e.g. feature/my-feature)"
  echo "  2) core/ (e.g. core/my-library)"
  echo "  3) Root level (no parent)"
  echo "  4) Custom (enter name)"
  read -rp "Choice [1-4]: " parent_choice
  case "$parent_choice" in
    1) PARENT="feature" ;;
    2) PARENT="core" ;;
    3) PARENT="" ;;
    4) read -rp "Enter custom parent folder name: " PARENT ;;
    *) die "Invalid choice" ;;
  esac
fi

if [[ -z "$NAME" ]]; then
  read -rp "Enter module name (e.g. login, database): " NAME
fi

# Clean and validate module name
if [[ -z "$NAME" ]]; then
  die "Module name cannot be empty"
fi

# Validate name (lowercase, numbers, hyphens only for module name)
if ! [[ "$NAME" =~ ^[a-z0-9-]+$ ]]; then
  die "Module name must contain only lowercase letters, digits, and hyphens (got: $NAME)"
fi

# Sanitize module name for package (no hyphens)
SANIZED_NAME_FOR_PKG="${NAME//-/}"

# Determine default package
if [[ -z "$PACKAGE" ]]; then
  if [[ -n "$PARENT" ]]; then
    # Sanitize parent for package (e.g. core/navigation -> core.navigation)
    CLEAN_PARENT_PKG="${PARENT//\//.}"
    CLEAN_PARENT_PKG="${CLEAN_PARENT_PKG//-/}"
    PACKAGE="app.template.${CLEAN_PARENT_PKG}.${SANIZED_NAME_FOR_PKG}"
  else
    PACKAGE="app.template.${SANIZED_NAME_FOR_PKG}"
  fi
  read -rp "Enter package name [default: $PACKAGE]: " package_input
  if [[ -n "$package_input" ]]; then
    PACKAGE="$package_input"
  fi
fi

# Validate package format
if ! [[ "$PACKAGE" =~ ^[a-z][a-z0-9_]*(\.[a-z][a-z0-9_]*)*$ ]]; then
  die "Package name must be a valid dotted identifier (got: $PACKAGE)"
fi

# ------------------------------ derived values --------------------------------

if [[ -n "$PARENT" ]]; then
  MODULE_DIR="${PARENT}/${NAME}"
  GRADLE_PATH=":${PARENT}:${NAME}"
else
  MODULE_DIR="${NAME}"
  GRADLE_PATH=":${NAME}"
fi

info "Creating module..."
note "Type:        $TYPE"
note "Name:        $NAME"
note "Location:    $MODULE_DIR"
note "Gradle Path: $GRADLE_PATH"
note "Package:     $PACKAGE"

# ------------------------------ file generation -------------------------------

if [[ -d "$MODULE_DIR" ]]; then
  die "Directory $MODULE_DIR already exists!"
fi

mkdir -p "$MODULE_DIR"

# Package directory subpath
PKG_PATH="${PACKAGE//./\/}"

# Create source directories
mkdir -p "${MODULE_DIR}/src/main/kotlin/${PKG_PATH}"
mkdir -p "${MODULE_DIR}/src/test/kotlin/${PKG_PATH}"

# Write build.gradle.kts
BUILD_GRADLE="${MODULE_DIR}/build.gradle.kts"

if [[ "$TYPE" == "android" ]]; then
  mkdir -p "${MODULE_DIR}/src/androidTest/kotlin/${PKG_PATH}"

  cat <<EOF > "$BUILD_GRADLE"
/*
 * Designed and developed by 2026 ashtanko (Oleksii Shtanko)
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 * http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */
plugins {
    alias(libs.plugins.androidlab.android.library)
    alias(libs.plugins.androidlab.android.library.compose)
    alias(libs.plugins.androidlab.android.library.jacoco)
    alias(libs.plugins.android.junit5)
}

android {
    namespace = "$PACKAGE"
}

dependencies {
    libs.apply {
        androidx.apply {
            api(material3)
            compose.apply {
                api(foundation)
                api(foundation.layout)
            }
        }

        junit5.apply {
            testImplementation(api)
            testImplementation(params)

            testRuntimeOnly(jupiterEngine)
        }
    }
}
EOF

  # AndroidManifest.xml
  mkdir -p "${MODULE_DIR}/src/main"
  cat <<EOF > "${MODULE_DIR}/src/main/AndroidManifest.xml"
<?xml version="1.0" encoding="utf-8"?>
<manifest xmlns:android="http://schemas.android.com/apk/res/android" />
EOF

  # Proguard files
  touch "${MODULE_DIR}/consumer-rules.pro"
  cat <<EOF > "${MODULE_DIR}/proguard-rules.pro"
# Add project specific ProGuard rules here.
EOF

else
  # Kotlin/JVM library
  cat <<EOF > "$BUILD_GRADLE"
/*
 * Designed and developed by 2026 ashtanko (Oleksii Shtanko)
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 * http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */
plugins {
    alias(libs.plugins.androidlab.jvm.library)
}

dependencies {
    testImplementation(libs.junit5.api)
    testRuntimeOnly(libs.junit5.jupiterEngine)
}
EOF
fi

# Write template source files
# 1) Main Class
CLASS_NAME=$(echo "$SANIZED_NAME_FOR_PKG" | awk '{print toupper(substr($0,1,1))substr($0,2)}')
cat <<EOF > "${MODULE_DIR}/src/main/kotlin/${PKG_PATH}/${CLASS_NAME}.kt"
/*
 * Designed and developed by 2026 ashtanko (Oleksii Shtanko)
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 * http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */
package $PACKAGE

/**
 * Placeholder class for the $NAME module.
 */
class ${CLASS_NAME}(
    private val moduleName: String = "$NAME",
) {
    fun greet(): String = "Hello from \$moduleName!"
}
EOF

# 2) Test Class
cat <<EOF > "${MODULE_DIR}/src/test/kotlin/${PKG_PATH}/${CLASS_NAME}Test.kt"
/*
 * Designed and developed by 2026 ashtanko (Oleksii Shtanko)
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 * http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */
package $PACKAGE

import org.junit.jupiter.api.Assertions.assertEquals
import org.junit.jupiter.api.Test

class ${CLASS_NAME}Test {
    @Test
    fun testGreet() {
        val module = ${CLASS_NAME}()
        assertEquals("Hello from $NAME!", module.greet())
    }
}
EOF

# -------------------- update settings.gradle.kts ------------------------------

info "Registering module in settings.gradle.kts..."

python3 - "$REPO_ROOT/settings.gradle.kts" "$GRADLE_PATH" "$PARENT" <<'EOF'
import sys
import re

file_path = sys.argv[1]
module_gradle_path = sys.argv[2]
parent = sys.argv[3]

with open(file_path, 'r') as f:
    content = f.read()

# Check if already included
if f'"{module_gradle_path}"' in content or f"'{module_gradle_path}'" in content:
    print("Module already included in settings.gradle.kts")
    sys.exit(0)

# If parent is provided
if parent:
    region_start = f"// region {parent}"
    region_end = "// endregion"

    # Try to find the region
    start_idx = content.find(region_start)
    if start_idx != -1:
        # Find the next endregion
        end_idx = content.find(region_end, start_idx)
        if end_idx != -1:
            before = content[:end_idx]
            after = content[end_idx:]

            # Match formatting (indentation)
            lines = before.splitlines()
            indent = ""
            if lines:
                last_line = lines[-1]
                match = re.match(r"^(\s*)", last_line)
                if match:
                    indent = match.group(1)

            new_content = before + f"{indent}include(\"{module_gradle_path}\")\n" + after
            with open(file_path, 'w') as f:
                f.write(new_content)
            print(f"Added {module_gradle_path} inside {region_start} region.")
            sys.exit(0)

# If region doesn't exist or no parent, append/insert at the end or create region
if parent:
    # Append a new region at the end
    new_region = f"\n// region {parent}\ninclude(\"{module_gradle_path}\")\n// endregion\n"
    with open(file_path, 'a') as f:
        f.write(new_region)
    print(f"Created region {parent} and added {module_gradle_path}")
else:
    # Just append include at the end of the root level
    lines = content.splitlines()
    last_include_idx = -1
    for idx, line in enumerate(lines):
        if line.strip().startswith("include("):
            last_include_idx = idx

    if last_include_idx != -1:
        lines.insert(last_include_idx + 1, f"include(\"{module_gradle_path}\")")
        new_content = "\n".join(lines) + "\n"
        with open(file_path, 'w') as f:
            f.write(new_content)
    else:
        with open(file_path, 'a') as f:
            f.write(f"\ninclude(\"{module_gradle_path}\")\n")
    print(f"Added {module_gradle_path} to settings.gradle.kts")
EOF

info "Done! Module created at $MODULE_DIR and registered in settings.gradle.kts."
note "Run './gradlew spotlessApply' to format the new files."
note "Run './gradlew :${PARENT}:${NAME}:test' to verify unit tests."
