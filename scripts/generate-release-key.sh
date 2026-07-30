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
readonly DEFAULT_KEYSTORE_PATH="release/upload-keystore.p12"
readonly DEFAULT_KEY_ALIAS="upload"
readonly DEFAULT_DISTINGUISHED_NAME="CN=Android Upload Key"
readonly KEY_VALIDITY_DAYS="10000"
readonly KEY_SIZE_BITS="4096"

KEYSTORE_INPUT=""
KEY_ALIAS=""
DISTINGUISHED_NAME=""
DRY_RUN=false
TEMP_DIRECTORY=""
KEYSTORE_INSTALLED=false
PROPERTIES_INSTALLED=false
COMPLETED=false

die() {
  printf '\033[31merror:\033[0m %s\n' "$*" >&2
  exit 1
}

info() {
  printf '\033[36m==>\033[0m %s\n' "$*"
}

note() {
  printf '    %s\n' "$*"
}

warn() {
  printf '\033[33mwarn:\033[0m %s\n' "$*" >&2
}

usage() {
  sed -n '/^# Usage:/,/^$/p' "$0" | sed 's/^# \{0,1\}//'
}

require_flag_value() {
  local flag="$1"
  local value="${2:-}"
  [[ -n "$value" && "$value" != --* ]] || die "$flag requires a value"
}

absolute_path() {
  local path="$1"
  if [[ "$path" == /* ]]; then
    printf '%s\n' "$path"
  else
    printf '%s/%s\n' "$REPO_ROOT" "$path"
  fi
}

escape_properties_value() {
  local value="$1"
  printf '%s' "${value//\\/\\\\}"
}

cleanup() {
  unset RELEASE_KEY_PASSWORD CONFIRM_RELEASE_KEY_PASSWORD

  if [[ "$COMPLETED" != true ]]; then
    if [[ "$PROPERTIES_INSTALLED" == true && -n "${PROPERTIES_PATH:-}" ]]; then
      rm -f -- "$PROPERTIES_PATH"
    fi
    if [[ "$KEYSTORE_INSTALLED" == true && -n "${KEYSTORE_PATH:-}" ]]; then
      rm -f -- "$KEYSTORE_PATH"
    fi
  fi

  if [[ -n "$TEMP_DIRECTORY" && -d "$TEMP_DIRECTORY" ]]; then
    rm -rf -- "$TEMP_DIRECTORY"
  fi
}

trap cleanup EXIT
trap 'exit 130' INT
trap 'exit 143' HUP TERM

# Usage:
#   scripts/generate-release-key.sh [options]
#
# Options:
#   --keystore PATH    Keystore output (default: release/upload-keystore.p12)
#   --alias NAME       Upload-key alias (default: upload)
#   --dname NAME       X.500 certificate name (default: CN=Android Upload Key)
#   --dry-run          Validate and print output paths without creating files
#   -h, --help         Show this help
#
# The script prompts for one password and uses it for both the keystore and key.
# For non-interactive use, provide RELEASE_KEY_PASSWORD through a protected
# environment rather than as a command-line argument.

while [[ $# -gt 0 ]]; do
  case "$1" in
    --keystore)
      require_flag_value "$1" "${2:-}"
      KEYSTORE_INPUT="$2"
      shift 2
      ;;
    --alias)
      require_flag_value "$1" "${2:-}"
      KEY_ALIAS="$2"
      shift 2
      ;;
    --dname)
      require_flag_value "$1" "${2:-}"
      DISTINGUISHED_NAME="$2"
      shift 2
      ;;
    --dry-run)
      DRY_RUN=true
      shift
      ;;
    -h | --help)
      usage
      exit 0
      ;;
    *)
      die "unknown option: $1 (try --help)"
      ;;
  esac
done

if [[ -z "$KEYSTORE_INPUT" ]]; then
  if [[ -t 0 ]]; then
    read -r -p "Keystore path [$DEFAULT_KEYSTORE_PATH]: " KEYSTORE_INPUT
  fi
  KEYSTORE_INPUT="${KEYSTORE_INPUT:-$DEFAULT_KEYSTORE_PATH}"
fi

if [[ -z "$KEY_ALIAS" ]]; then
  if [[ -t 0 ]]; then
    read -r -p "Key alias [$DEFAULT_KEY_ALIAS]: " KEY_ALIAS
  fi
  KEY_ALIAS="${KEY_ALIAS:-$DEFAULT_KEY_ALIAS}"
fi

if [[ -z "$DISTINGUISHED_NAME" ]]; then
  if [[ -t 0 ]]; then
    read -r -p "Certificate name [$DEFAULT_DISTINGUISHED_NAME]: " DISTINGUISHED_NAME
  fi
  DISTINGUISHED_NAME="${DISTINGUISHED_NAME:-$DEFAULT_DISTINGUISHED_NAME}"
fi

[[ "$KEYSTORE_INPUT" != *$'\n'* ]] || die "keystore path must not contain a newline"
[[ "$DISTINGUISHED_NAME" != *$'\n'* ]] || die "certificate name must not contain a newline"
[[ "$KEY_ALIAS" =~ ^[A-Za-z0-9._-]+$ ]] ||
  die "alias may contain only letters, digits, dots, underscores, and hyphens"

case "$KEYSTORE_INPUT" in
  *.p12 | *.pfx) ;;
  *) die "new keystore path must end in .p12 or .pfx" ;;
esac

KEYSTORE_PATH="$(absolute_path "$KEYSTORE_INPUT")"
PROPERTIES_PATH="$REPO_ROOT/key.properties"

[[ ! -e "$KEYSTORE_PATH" ]] || die "refusing to overwrite existing keystore: $KEYSTORE_PATH"
[[ ! -e "$PROPERTIES_PATH" ]] || die "refusing to overwrite existing file: $PROPERTIES_PATH"

command -v keytool >/dev/null 2>&1 ||
  die "keytool was not found; install or select the repository's required JDK 21"

info "Upload-key configuration"
note "Keystore:    $KEYSTORE_PATH"
note "Properties:  $PROPERTIES_PATH"
note "Alias:       $KEY_ALIAS"
note "Certificate: $DISTINGUISHED_NAME"
note "Format:      PKCS12"
note "Algorithm:   RSA $KEY_SIZE_BITS / SHA-256"
note "Validity:    $KEY_VALIDITY_DAYS days"

if [[ "$DRY_RUN" == true ]]; then
  warn "dry run; no key or properties file was created"
  exit 0
fi

if [[ -z "${RELEASE_KEY_PASSWORD:-}" ]]; then
  [[ -t 0 ]] || die "interactive password input requires a terminal"
  read -r -s -p "Keystore and key password (12+ visible ASCII characters): " \
    RELEASE_KEY_PASSWORD
  printf '\n'
  read -r -s -p "Confirm password: " CONFIRM_RELEASE_KEY_PASSWORD
  printf '\n'
  [[ "$RELEASE_KEY_PASSWORD" == "$CONFIRM_RELEASE_KEY_PASSWORD" ]] ||
    die "passwords do not match"
fi

LC_ALL=C
export LC_ALL
[[ "$RELEASE_KEY_PASSWORD" =~ ^[[:graph:]]{12,}$ ]] ||
  die "password must contain at least 12 visible ASCII characters and no spaces"

mkdir -p -- "$(dirname "$KEYSTORE_PATH")" "$(dirname "$PROPERTIES_PATH")"
TEMP_DIRECTORY="$(mktemp -d "${TMPDIR:-/tmp}/android-upload-key.XXXXXX")"
readonly TEMP_KEYSTORE="$TEMP_DIRECTORY/upload-keystore.p12"
readonly TEMP_PROPERTIES="$TEMP_DIRECTORY/key.properties"

umask 077
export RELEASE_KEY_PASSWORD

info "Generating upload key"
keytool -genkeypair \
  -keystore "$TEMP_KEYSTORE" \
  -storetype PKCS12 \
  -storepass:env RELEASE_KEY_PASSWORD \
  -keypass:env RELEASE_KEY_PASSWORD \
  -alias "$KEY_ALIAS" \
  -keyalg RSA \
  -keysize "$KEY_SIZE_BITS" \
  -sigalg SHA256withRSA \
  -validity "$KEY_VALIDITY_DAYS" \
  -dname "$DISTINGUISHED_NAME"

keytool -list \
  -keystore "$TEMP_KEYSTORE" \
  -storepass:env RELEASE_KEY_PASSWORD \
  -alias "$KEY_ALIAS" >/dev/null

{
  printf '# Generated by scripts/generate-release-key.sh. Do not commit this file.\n'
  printf 'storeFile=%s\n' "$(escape_properties_value "$KEYSTORE_PATH")"
  printf 'storePassword=%s\n' "$(escape_properties_value "$RELEASE_KEY_PASSWORD")"
  printf 'keyAlias=%s\n' "$KEY_ALIAS"
  printf 'keyPassword=%s\n' "$(escape_properties_value "$RELEASE_KEY_PASSWORD")"
} > "$TEMP_PROPERTIES"

[[ ! -e "$KEYSTORE_PATH" ]] || die "keystore appeared while generating; refusing to overwrite it"
mv -- "$TEMP_KEYSTORE" "$KEYSTORE_PATH"
KEYSTORE_INSTALLED=true
chmod 600 "$KEYSTORE_PATH"

[[ ! -e "$PROPERTIES_PATH" ]] ||
  die "properties file appeared while generating; refusing to overwrite it"
mv -- "$TEMP_PROPERTIES" "$PROPERTIES_PATH"
PROPERTIES_INSTALLED=true
chmod 600 "$PROPERTIES_PATH"

COMPLETED=true
unset RELEASE_KEY_PASSWORD CONFIRM_RELEASE_KEY_PASSWORD

info "Upload key created"
note "Keystore:   $KEYSTORE_PATH"
note "Properties: $PROPERTIES_PATH"
note "Build:      make release"
warn "Back up the keystore and password in separate secure locations before publishing."
