#!/usr/bin/env bash
# rename-template.sh — bootstrap a project from this template.
#
# Usage:
#   scripts/rename-template.sh \
#     --package com.example.myapp \
#     --name "My Awesome App" \
#     [--plugin-alias myapp] \
#     [--author "Jane Doe"] \
#     [--dry-run] \
#     [--verbose] \
#     [--force]
#
# Run from the repository root or any subdirectory. The implementation keeps
# this shell entry point portable while using Python's standard library for
# safe, format-aware text replacement and transactional file moves.

set -euo pipefail

readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

command -v python3 >/dev/null 2>&1 || {
  printf '\033[31merror:\033[0m Python 3.8 or newer is required to rename the template\n' >&2
  exit 1
}

python3 -c 'import sys; raise SystemExit(sys.version_info < (3, 8))' || {
  printf '\033[31merror:\033[0m Python 3.8 or newer is required to rename the template\n' >&2
  exit 1
}

exec python3 "$SCRIPT_DIR/rename-template.py" "$@"
