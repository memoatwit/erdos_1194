#!/bin/bash

set -euo pipefail

DOI=${DOI:-10.5281/zenodo.21413746}
UPLOAD_DIR=${UPLOAD_DIR:-/scratch4/workspace/ergezerm_wit_edu-soft_speech/r3_212_zenodo_v2_upload}
TOKEN_FILE=${TOKEN_FILE:-$HOME/.config/zenodo/r3_v2_token}

[ -d "$UPLOAD_DIR" ] || { echo "missing upload directory: $UPLOAD_DIR" >&2; exit 1; }
[ -s "$TOKEN_FILE" ] || { echo "missing token file: $TOKEN_FILE" >&2; exit 1; }

TOKEN_MODE=$(stat -c '%a' "$TOKEN_FILE")
if [ "$TOKEN_MODE" != "600" ] && [ "$TOKEN_MODE" != "400" ]; then
  echo "token file must have mode 600 or 400, found $TOKEN_MODE" >&2
  exit 1
fi

TOKEN=$(<"$TOKEN_FILE")
DEPOSITS=$(mktemp)
DRAFT=$(mktemp)
CURL_CONFIG=$(mktemp)
chmod 600 "$CURL_CONFIG"
printf 'header = "Authorization: Bearer %s"\n' "$TOKEN" > "$CURL_CONFIG"
unset TOKEN
trap 'rm -f "$DEPOSITS" "$DRAFT" "$CURL_CONFIG"' EXIT

curl --fail --silent --show-error \
  --retry 5 \
  --config "$CURL_CONFIG" \
  -o "$DEPOSITS" \
  "https://zenodo.org/api/deposit/depositions?status=draft&all_versions=true&size=100"

DEPOSITION_ID=$(jq -r --arg doi "$DOI" '
  .[]
  | select(
      .metadata.prereserve_doi.doi == $doi
      or .doi == $doi
      or .metadata.doi == $doi
    )
  | .id
' "$DEPOSITS" | head -n 1)

if [ -z "$DEPOSITION_ID" ] || [ "$DEPOSITION_ID" = "null" ]; then
  echo "could not find a draft deposition for reserved DOI $DOI" >&2
  exit 1
fi

curl --fail --silent --show-error \
  --retry 5 \
  --config "$CURL_CONFIG" \
  -o "$DRAFT" \
  "https://zenodo.org/api/deposit/depositions/$DEPOSITION_ID"

BUCKET=$(jq -r '.links.bucket' "$DRAFT")
[ -n "$BUCKET" ] && [ "$BUCKET" != "null" ] || {
  echo "draft deposition $DEPOSITION_ID has no upload bucket" >&2
  exit 1
}

echo "Draft DOI: $DOI"
echo "Upload directory: $UPLOAD_DIR"
echo "Bucket: $BUCKET"

shopt -s nullglob
FILES=(
  "$UPLOAD_DIR"/*.tar.zst
  "$UPLOAD_DIR"/r3-*.tar.zst.sha256
  "$UPLOAD_DIR"/MANIFEST.sha256
)
[ ${#FILES[@]} -gt 0 ] || { echo "no release files found" >&2; exit 1; }

for file in "${FILES[@]}"; do
  name=$(basename "$file")
  local_size=$(stat -c '%s' "$file")
  remote_size=$(jq -r --arg name "$name" '
    [
      .files[]?
      | select((.filename // .key) == $name)
      | (.filesize // .size)
    ][0] // empty
  ' "$DRAFT")

  if [ -n "$remote_size" ]; then
    if [ "$remote_size" = "$local_size" ]; then
      echo "[skip] $name already exists with matching size ($local_size bytes)"
      continue
    fi
    echo "remote file $name has size $remote_size; local size is $local_size" >&2
    echo "refusing to overwrite a mismatched draft file" >&2
    exit 1
  fi

  echo "[upload] $name ($local_size bytes)"
  curl --fail --show-error \
    --retry 10 \
    --retry-all-errors \
    --connect-timeout 60 \
    --config "$CURL_CONFIG" \
    --upload-file "$file" \
    "$BUCKET/$name"
  echo
done

echo "Upload complete. Review the Zenodo draft in the web interface; this script does not publish it."
