#!/usr/bin/env bash
# validate-rename.sh — verify a project was fully renamed from this template.
#
# Run this after scripts/rename-template.sh to confirm that no original template
# identity values remain, that source folders match the new package, that
# scripts/template-identity.json is internally consistent, and that the touched
# Android string resources still parse as XML.
#
# Usage:
#   scripts/validate-rename.sh [--verbose]
#
# Run from the repository root or any subdirectory. Exits non-zero and lists
# every problem found when validation fails. The implementation keeps this shell
# entry point portable while using Python's standard library for the checks.

set -euo pipefail

readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

command -v python3 >/dev/null 2>&1 || {
  printf '\033[31merror:\033[0m Python 3.8 or newer is required to validate the rename\n' >&2
  exit 1
}

python3 -c 'import sys; raise SystemExit(sys.version_info < (3, 8))' || {
  printf '\033[31merror:\033[0m Python 3.8 or newer is required to validate the rename\n' >&2
  exit 1
}

exec python3 "$SCRIPT_DIR/validate-rename.py" "$@"
