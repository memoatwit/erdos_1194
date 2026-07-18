#!/bin/bash

set -euo pipefail

DRAFT_ID=${DRAFT_ID:-21413746}
V1_ID=${V1_ID:-20463334}
UPLOAD_DIR=${UPLOAD_DIR:-/scratch4/workspace/ergezerm_wit_edu-soft_speech/r3_212_zenodo_v2_upload}
TOKEN_FILE=${TOKEN_FILE:-$HOME/.config/zenodo/r3_v2_token}

[ -d "$UPLOAD_DIR" ] || { echo "missing upload directory: $UPLOAD_DIR" >&2; exit 1; }
[ -s "$TOKEN_FILE" ] || { echo "missing token file: $TOKEN_FILE" >&2; exit 1; }

TOKEN_MODE=$(stat -c '%a' "$TOKEN_FILE")
if [ "$TOKEN_MODE" != "600" ] && [ "$TOKEN_MODE" != "400" ]; then
  echo "token file must have mode 600 or 400, found $TOKEN_MODE" >&2
  exit 1
fi

ZENODO_CACHE_DIR=${ZENODO_CACHE_DIR:-$HOME/.cache/zenodo}
mkdir -p "$ZENODO_CACHE_DIR"
chmod 700 "$ZENODO_CACHE_DIR"
TMPDIR_RUN=$(mktemp -d "$ZENODO_CACHE_DIR/r3-v2-import.XXXXXX")
CURL_CONFIG="$TMPDIR_RUN/curl.conf"
: > "$CURL_CONFIG"
chmod 600 "$CURL_CONFIG"
TOKEN=$(<"$TOKEN_FILE")
printf 'header = "Authorization: Bearer %s"\n' "$TOKEN" > "$CURL_CONFIG"
unset TOKEN
trap 'rm -rf "$TMPDIR_RUN"' EXIT

api_get() {
  curl --fail --silent --show-error --retry 5 --config "$CURL_CONFIG" "$1"
}

api_delete() {
  local url=$1
  local code
  code=$(curl --silent --show-error --retry 5 --config "$CURL_CONFIG" \
    -X DELETE -o /dev/null -w '%{http_code}' "$url")
  [ "$code" = "204" ] || {
    echo "DELETE $url returned HTTP $code" >&2
    exit 1
  }
}

DRAFT_BEFORE="$TMPDIR_RUN/draft-before.json"
V1_RECORD="$TMPDIR_RUN/v1-record.json"
EXPECTED_NEW="$TMPDIR_RUN/expected-new.tsv"
ACTUAL_NEW="$TMPDIR_RUN/actual-new.tsv"

api_get "https://zenodo.org/api/deposit/depositions/$DRAFT_ID" > "$DRAFT_BEFORE"
curl --fail --silent --show-error --retry 5 \
  "https://zenodo.org/api/records/$V1_ID" > "$V1_RECORD"

(
  cd "$UPLOAD_DIR"
  for file in r3-*.tar.zst r3-*.tar.zst.sha256 MANIFEST.sha256; do
    printf '%s\t%s\n' "$file" "$(stat -c '%s' "$file")"
  done
) | sort > "$EXPECTED_NEW"

jq -r '.files[] | [.filename, (.filesize | tonumber)] | @tsv' \
  "$DRAFT_BEFORE" | sort > "$ACTUAL_NEW"

if ! cmp -s "$EXPECTED_NEW" "$ACTUAL_NEW"; then
  echo "draft files do not exactly match the verified Unity release set" >&2
  diff -u "$EXPECTED_NEW" "$ACTUAL_NEW" >&2 || true
  exit 1
fi

echo "[verified] current draft contains exactly the nine v2 release files"

while IFS=$'\t' read -r file_id filename; do
  echo "[remove temporarily] $filename"
  api_delete "https://zenodo.org/api/deposit/depositions/$DRAFT_ID/files/$file_id"
done < <(jq -r '.files[] | [.id, .filename] | @tsv' "$DRAFT_BEFORE")

EMPTY_DRAFT="$TMPDIR_RUN/empty-draft.json"
api_get "https://zenodo.org/api/records/$DRAFT_ID/draft" > "$EMPTY_DRAFT"
[ "$(jq '.files | length' "$EMPTY_DRAFT")" = "0" ] || {
  echo "draft was not empty after temporary removals" >&2
  exit 1
}

echo "[import] linking files from v1 record $V1_ID"
IMPORT_RESPONSE="$TMPDIR_RUN/import-response.json"
IMPORT_CODE=$(curl --silent --show-error --retry 5 --config "$CURL_CONFIG" \
  -X POST -o "$IMPORT_RESPONSE" -w '%{http_code}' \
  "https://zenodo.org/api/records/$DRAFT_ID/draft/actions/files-import")
if [ "$IMPORT_CODE" != "201" ] && [ "$IMPORT_CODE" != "200" ]; then
  echo "file import returned HTTP $IMPORT_CODE" >&2
  cat "$IMPORT_RESPONSE" >&2
  exit 1
fi

IMPORTED_DRAFT="$TMPDIR_RUN/imported-draft.json"
V1_EXPECTED="$TMPDIR_RUN/v1-expected.tsv"
V1_ACTUAL="$TMPDIR_RUN/v1-actual.tsv"
api_get "https://zenodo.org/api/records/$DRAFT_ID/draft" > "$IMPORTED_DRAFT"

jq -r '.files[] | [.key, (.size | tostring), .checksum] | @tsv' \
  "$V1_RECORD" | sort > "$V1_EXPECTED"
jq -r '.files[] | [.key, (.size | tostring), .checksum] | @tsv' \
  "$IMPORTED_DRAFT" | sort > "$V1_ACTUAL"

if ! cmp -s "$V1_EXPECTED" "$V1_ACTUAL"; then
  echo "imported files do not exactly match v1" >&2
  diff -u "$V1_EXPECTED" "$V1_ACTUAL" >&2 || true
  exit 1
fi

echo "[verified] all 12 v1 files linked with matching sizes and checksums"
echo "[remove obsolete] upload_probe.txt"
api_delete "https://zenodo.org/api/records/$DRAFT_ID/draft/files/upload_probe.txt"

FINAL_DRAFT="$TMPDIR_RUN/final-draft.json"
api_get "https://zenodo.org/api/records/$DRAFT_ID/draft" > "$FINAL_DRAFT"

if jq -e '.files[] | select(.key == "upload_probe.txt")' "$FINAL_DRAFT" >/dev/null; then
  echo "upload_probe.txt still exists" >&2
  exit 1
fi

[ "$(jq '.files | length' "$FINAL_DRAFT")" = "11" ] || {
  echo "expected 11 retained v1 files" >&2
  exit 1
}

echo "[complete] 11 retained v1 files are linked; the nine v2 files can now be re-uploaded"
