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

readonly REPO_ROOT="$(git rev-parse --show-toplevel)"
readonly PRIVATE_KEY_PATTERN="-----BEGIN ([A-Z0-9]+ )?PRIVATE"" KEY-----"
readonly KNOWN_TOKEN_PATTERN="(AKIA[0-9A-Z]{16}|AIza[0-9A-Za-z_-]{35}|gh[pousr]_[0-9A-Za-z]{36,}|github_pat_[0-9A-Za-z_]{50,}|xox[baprs]-[0-9A-Za-z-]{20,}|sk_live_[0-9A-Za-z]{20,}|npm_[0-9A-Za-z]{36,}|sk-(proj-)?[0-9A-Za-z_-]{32,})"
readonly GRADLE_SIGNING_PASSWORD_PATTERN="(storePassword|keyPassword)[[:space:]]*=[[:space:]]*['\"][^'\"]+['\"]"
readonly PROPERTIES_SIGNING_PASSWORD_PATTERN="^(storePassword|keyPassword)[[:space:]]*[:=][[:space:]]*[^[:space:]]+"

MODE="all"
failures=0

usage() {
  printf '%s\n' \
    "Usage: scripts/check-secrets.sh [--all|--staged]" \
    "" \
    "  --all     Scan every file in the Git index (default; use in CI)." \
    "  --staged  Scan only added, copied, modified, or renamed staged files."
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --all)
      MODE="all"
      ;;
    --staged)
      MODE="staged"
      ;;
    -h | --help)
      usage
      exit 0
      ;;
    *)
      printf 'error: unknown option: %s\n' "$1" >&2
      usage >&2
      exit 2
      ;;
  esac
  shift
done

cd "$REPO_ROOT"

forbidden_path_reason() {
  local path="$1"
  local basename="${path##*/}"

  # This repository intentionally tracks one public template debug key.
  if [[ "$path" == "release/app-debug.jks" ]]; then
    return 1
  fi

  case "$basename" in
    key.properties | keystore.properties | secrets.properties | credentials.properties)
      printf 'credential properties file'
      return 0
      ;;
    local.properties)
      printf 'machine-local Android configuration'
      return 0
      ;;
    .env.example | .env.sample | .env.template)
      return 1
      ;;
    .env | .env.*)
      printf 'environment file'
      return 0
      ;;
    id_rsa | id_dsa | id_ecdsa | id_ed25519)
      printf 'SSH private key'
      return 0
      ;;
    service-account*.json | service_account*.json | *-service-account.json)
      printf 'service-account credential file'
      return 0
      ;;
  esac

  case "$path" in
    *.jks | *.JKS | *.keystore | *.p12 | *.pfx | *.P12 | *.PFX)
      printf 'private keystore container'
      return 0
      ;;
    *keystore*.base64 | *keystore*.b64)
      printf 'encoded keystore'
      return 0
      ;;
  esac

  return 1
}

index_blob_matches() {
  local path="$1"
  local pattern="$2"

  # Do not use grep -q here: with pipefail it can terminate git cat-file with
  # SIGPIPE and hide a successful match.
  git cat-file blob ":$path" 2>/dev/null |
    LC_ALL=C grep -aE -- "$pattern" >/dev/null
}

report_content_failure() {
  local path="$1"
  local rule="$2"

  printf 'error: suspected secret in %q (rule: %s)\n' "$path" "$rule" >&2
  failures=$((failures + 1))
}

scan_path() {
  local path="$1"
  local reason

  if reason="$(forbidden_path_reason "$path")"; then
    printf 'error: forbidden sensitive path %q (%s)\n' "$path" "$reason" >&2
    failures=$((failures + 1))
    return
  fi

  # The allowlisted template debug keystore is binary and intentionally
  # insecure; it is never valid release signing material.
  if [[ "$path" == "release/app-debug.jks" ]]; then
    return
  fi

  if index_blob_matches "$path" "$PRIVATE_KEY_PATTERN"; then
    report_content_failure "$path" "private-key material"
  fi

  if index_blob_matches "$path" "$KNOWN_TOKEN_PATTERN"; then
    report_content_failure "$path" "known token format"
  fi

  case "$path" in
    *.gradle | *.gradle.kts)
      if index_blob_matches "$path" "$GRADLE_SIGNING_PASSWORD_PATTERN"; then
        report_content_failure "$path" "hardcoded Android signing password"
      fi
      ;;
    *.properties)
      if index_blob_matches "$path" "$PROPERTIES_SIGNING_PASSWORD_PATTERN"; then
        report_content_failure "$path" "hardcoded Android signing password"
      fi
      ;;
  esac
}

list_paths() {
  if [[ "$MODE" == "staged" ]]; then
    git diff --cached --name-only --diff-filter=ACMR -z
  else
    git ls-files -z
  fi
}

while IFS= read -r -d '' path; do
  scan_path "$path"
done < <(list_paths)

if ((failures > 0)); then
  printf '\nSecret scan failed with %d finding(s).\n' "$failures" >&2
  printf '%s\n' \
    "Remove the file or credential from the commit. If a real secret was" \
    "ever committed, revoke or rotate it; deleting it in a later commit is" \
    "not sufficient. Review false positives instead of bypassing the check." >&2
  exit 1
fi

if [[ "$MODE" == "staged" ]]; then
  printf 'Staged secret check passed.\n'
else
  printf 'Tracked secret check passed.\n'
fi
