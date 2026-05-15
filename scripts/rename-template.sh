#!/usr/bin/env bash
# rename-template.sh — bootstrap a new project from this template by renaming
# every package, applicationId, plugin alias, display name, folder, and
# (optionally) copyright header to the values you provide.
#
# Usage:
#   scripts/rename-template.sh \
#     --package com.example.myapp \
#     --name    "My Awesome App" \
#     [--plugin-alias myapp] \
#     [--author "Jane Doe"] \
#     [--dry-run] \
#     [--force]
#
# Run from the repo root or any subdirectory — the script resolves the root
# from its own location.

set -euo pipefail

# ------------------------------ helpers ---------------------------------------

die()  { printf '\033[31merror:\033[0m %s\n' "$*" >&2; exit 1; }
info() { printf '\033[36m==>\033[0m %s\n' "$*"; }
note() { printf '    %s\n' "$*"; }
warn() { printf '\033[33mwarn:\033[0m %s\n' "$*" >&2; }

# Cross-platform in-place sed. GNU sed accepts `sed -i ''` only with an empty
# arg; BSD sed (macOS) requires it. Detect once and shim.
if sed --version >/dev/null 2>&1; then
  sed_inplace() { sed -i "$@"; }
else
  sed_inplace() { sed -i '' "$@"; }
fi

# ------------------------------ args ------------------------------------------

NEW_PACKAGE=""
NEW_NAME=""
PLUGIN_ALIAS=""
AUTHOR=""
DRY_RUN=0
FORCE=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --package)       NEW_PACKAGE="$2"; shift 2 ;;
    --name)          NEW_NAME="$2"; shift 2 ;;
    --plugin-alias)  PLUGIN_ALIAS="$2"; shift 2 ;;
    --author)        AUTHOR="$2"; shift 2 ;;
    --dry-run)       DRY_RUN=1; shift ;;
    --force)         FORCE=1; shift ;;
    -h|--help)
      sed -n '2,15p' "$0" | sed 's/^# \{0,1\}//'
      exit 0 ;;
    *) die "unknown flag: $1 (try --help)" ;;
  esac
done

[[ -n "$NEW_PACKAGE" ]] || die "--package is required (e.g. com.example.myapp)"
[[ -n "$NEW_NAME"    ]] || die "--name is required (e.g. \"My App\")"

if ! [[ "$NEW_PACKAGE" =~ ^[a-z][a-z0-9_]*(\.[a-z][a-z0-9_]*)+$ ]]; then
  die "--package must be a valid lowercase dotted identifier (got: $NEW_PACKAGE)"
fi

# Derived values.
NEW_PKG_PATH="${NEW_PACKAGE//./\/}"
NEW_BUILDLOGIC="${NEW_PACKAGE}.buildlogic"
NEW_BUILDLOGIC_PATH="${NEW_BUILDLOGIC//./\/}"
PLUGIN_ALIAS="${PLUGIN_ALIAS:-${NEW_PACKAGE##*.}}"

# Reject plugin-alias collisions with known top-level plugin ids.
case "$PLUGIN_ALIAS" in
  android|kotlin|java|compose|gradle)
    die "--plugin-alias '$PLUGIN_ALIAS' collides with a reserved plugin id; pass --plugin-alias explicitly"
    ;;
esac

# ------------------------------ pre-flight ------------------------------------

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

IN_GIT=0
if git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  IN_GIT=1
  if [[ -n "$(git status --porcelain)" && "$FORCE" -eq 0 ]]; then
    die "working tree has uncommitted changes; commit/stash first or pass --force"
  fi
fi

info "repo root:      $REPO_ROOT"
info "new package:    $NEW_PACKAGE  (path: $NEW_PKG_PATH)"
info "new name:       $NEW_NAME"
info "plugin alias:   $PLUGIN_ALIAS"
info "build-logic:    $NEW_BUILDLOGIC  (path: $NEW_BUILDLOGIC_PATH)"
[[ -n "$AUTHOR" ]] && info "author:         $AUTHOR" || note "author rewrite: skipped (pass --author to enable)"
[[ "$DRY_RUN" -eq 1 ]] && warn "DRY RUN — no files will be modified"

# ------------------------------ string replacement ----------------------------

# replace_in <pattern> <replacement> <find-args...>
# Finds files matching the trailing find args, scans them for the pattern,
# and rewrites in place (or prints under dry-run).
replace_in() {
  local pattern="$1" replacement="$2"; shift 2
  local match_count=0 file
  # Escape sed special chars in pattern and replacement (we use | as delimiter).
  local pat_esc rep_esc
  pat_esc=$(printf '%s' "$pattern"     | sed 's/[][\\.^$*/|&]/\\&/g')
  rep_esc=$(printf '%s' "$replacement" | sed 's/[\\/&|]/\\&/g')

  while IFS= read -r -d '' file; do
    if grep -q -F -- "$pattern" "$file"; then
      match_count=$((match_count + 1))
      if [[ "$DRY_RUN" -eq 1 ]]; then
        local hits
        hits=$(grep -c -F -- "$pattern" "$file" || true)
        note "would rewrite ($hits hits): ${file#"$REPO_ROOT/"}"
      else
        sed_inplace "s|${pat_esc}|${rep_esc}|g" "$file"
      fi
    fi
  done < <(find "$@" -print0)

  printf '    %d file(s) %s pattern: %s\n' "$match_count" \
    "$([[ $DRY_RUN -eq 1 ]] && echo 'would change for' || echo 'rewritten for')" "$pattern"
}

info "rewriting strings..."

# 1a) dev.shtanko.androidlab.buildlogic -> <new>.buildlogic  (specific case first
#     so the group declaration doesn't end up with a double .buildlogic suffix)
replace_in "dev.shtanko.androidlab.buildlogic" "$NEW_BUILDLOGIC" \
  build-logic -type f \( -name '*.kt' -o -name '*.kts' \)

# 1b) dev.shtanko.androidlab -> <new>.buildlogic   (must run before dev.shtanko.template)
replace_in "dev.shtanko.androidlab" "$NEW_BUILDLOGIC" \
  build-logic -type f \( -name '*.kt' -o -name '*.kts' \)

# 2) dev.shtanko.template -> <new>
replace_in "dev.shtanko.template" "$NEW_PACKAGE" \
  . -type f \( -name '*.kt' -o -name '*.kts' -o -name 'AndroidManifest.xml' -o -name '*.pro' \) \
  -not -path './build/*' -not -path './*/build/*' -not -path './.git/*' -not -path './scripts/*'

# 3) app.template -> <new>
replace_in "app.template" "$NEW_PACKAGE" \
  . -type f \( -name '*.kt' -o -name '*.kts' -o -name 'AndroidManifest.xml' \) \
  -not -path './build/*' -not -path './*/build/*' -not -path './.git/*' -not -path './scripts/*'

# 4) androidlab plugin alias -> <plugin-alias>
#    Scoped to: version catalog, every build.gradle.kts, AND build-logic .kt files
#    (which embed plugin ids as string literals like "androidlab.android.lint").
#    Safe to run last because step 1 already rewrote every `dev.shtanko.androidlab`
#    qualifier — what remains as bare `androidlab` is always a plugin id.
replace_in "androidlab" "$PLUGIN_ALIAS" \
  gradle/libs.versions.toml

replace_in "androidlab" "$PLUGIN_ALIAS" \
  . -type f -name 'build.gradle.kts' \
  -not -path './build/*' -not -path './*/build/*' -not -path './.git/*'

replace_in "androidlab" "$PLUGIN_ALIAS" \
  build-logic -type f -name '*.kt'

# 5) Display names
if [[ -f settings.gradle.kts ]] && grep -q '"Android Template"' settings.gradle.kts; then
  if [[ "$DRY_RUN" -eq 1 ]]; then
    note "would rewrite display name in: settings.gradle.kts"
  else
    sed_inplace "s|\"Android Template\"|\"${NEW_NAME//\"/\\\"}\"|g" settings.gradle.kts
  fi
fi

STRINGS_XML="app/src/main/res/values/strings.xml"
if [[ -f "$STRINGS_XML" ]] && grep -q "Compose Android Template" "$STRINGS_XML"; then
  if [[ "$DRY_RUN" -eq 1 ]]; then
    note "would rewrite app_name in: $STRINGS_XML"
  else
    sed_inplace "s|Compose Android Template|${NEW_NAME}|g" "$STRINGS_XML"
  fi
fi

# 6) Optional author rewrite
if [[ -n "$AUTHOR" ]]; then
  info "rewriting author/copyright headers..."
  replace_in "ashtanko (Oleksii Shtanko)" "$AUTHOR" \
    . -type f \( -name '*.kt' -o -name '*.kts' -o -name '*.xml' \) \
    -not -path './build/*' -not -path './*/build/*' -not -path './.git/*'
fi

# ------------------------------ directory moves -------------------------------

mover() {
  local src="$1" dst="$2"
  [[ -d "$src" ]] || { note "skip move (missing): $src"; return 0; }
  if [[ -e "$dst" ]]; then
    note "skip move (target exists): $dst"
    return 0
  fi
  if [[ "$DRY_RUN" -eq 1 ]]; then
    note "would move: $src -> $dst"
    return 0
  fi
  mkdir -p "$(dirname "$dst")"
  if [[ "$IN_GIT" -eq 1 ]]; then
    git mv "$src" "$dst"
  else
    mv "$src" "$dst"
  fi
}

info "moving source directories..."

# Find source root (kotlin/ or java/) under a given module sourceset, then move
# the old package path to the new package path inside it.
# Args: <module>/<sourceset>  <old-pkg-subpath>  <new-pkg-subpath>
mover_module() {
  local moduleset="$1" old_sub="$2" new_sub="$3" lang
  for lang in kotlin java; do
    local src="${moduleset}/${lang}/${old_sub}"
    local dst="${moduleset}/${lang}/${new_sub}"
    if [[ -d "$src" ]]; then
      mover "$src" "$dst"
    fi
  done
}

mover_module "buildSrc/src/main"                "dev/shtanko/template"          "${NEW_PKG_PATH}"
mover_module "benchmarks/src/main"              "dev/shtanko/template/benchmarks" "${NEW_PKG_PATH}/benchmarks"
mover_module "build-logic/convention/src/main"  "dev/shtanko/androidlab"        "${NEW_BUILDLOGIC_PATH}"

mover_module "app/src/main"        "app/template" "${NEW_PKG_PATH}"
mover_module "app/src/androidTest" "app/template" "${NEW_PKG_PATH}"

for sourceset in main test androidTest; do
  mover_module "library-android/src/${sourceset}" \
               "app/template/library/android" \
               "${NEW_PKG_PATH}/library/android"
done

for sourceset in main test; do
  mover_module "library-kotlin/src/${sourceset}" \
               "app/template" \
               "${NEW_PKG_PATH}"
done

# ------------------------------ cleanup empty parents -------------------------

info "pruning empty parent directories..."
prune_parents() {
  local dir="$1"
  [[ -d "$dir" ]] || return 0
  if [[ "$DRY_RUN" -eq 1 ]]; then
    find "$dir" -type d -empty -print 2>/dev/null | sed 's|^|    would remove: |' || true
    return 0
  fi
  find "$dir" -type d -empty -delete 2>/dev/null || true
}

# Old package paths that may now be empty parent shells. Wildcards over
# kotlin/ and java/ cover the mixed source-set layout.
for root in \
  buildSrc/src/main/kotlin/dev/shtanko \
  benchmarks/src/main/java/dev/shtanko \
  build-logic/convention/src/main/kotlin/dev/shtanko \
  app/src/*/kotlin/app \
  app/src/*/java/app \
  library-android/src/*/kotlin/app \
  library-android/src/*/java/app \
  library-kotlin/src/*/kotlin/app \
  library-kotlin/src/*/java/app; do
  for expanded in $root; do
    prune_parents "$expanded"
  done
done

# ------------------------------ done ------------------------------------------

info "done."
if [[ "$DRY_RUN" -eq 1 ]]; then
  warn "this was a DRY RUN — re-run without --dry-run to apply"
else
  cat <<EOF

next steps:
  1. review changes:        git status && git diff
  2. apply copyright/format ./gradlew spotlessApply
  3. verify build:          ./gradlew clean assembleDebug
  4. commit:                git add -A && git commit -m "Initialize project: ${NEW_NAME}"
EOF
fi
