#!/usr/bin/env bash
# Launch the project setup wizard with Python's standard library only.

set -euo pipefail

readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

command -v python3 >/dev/null 2>&1 || {
  printf '\033[31merror:\033[0m Python 3.8 or newer is required\n' >&2
  exit 1
}

python3 -c 'import sys; raise SystemExit(sys.version_info < (3, 8))' || {
  printf '\033[31merror:\033[0m Python 3.8 or newer is required\n' >&2
  exit 1
}

exec python3 "$SCRIPT_DIR/setup-project.py" "$@"
