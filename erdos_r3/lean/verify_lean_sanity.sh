#!/usr/bin/env bash
set -euo pipefail

# Sanity-check the r_3(212) Lean benchmark files.
#
# Default behavior:
#   - create a temporary `lake new R3 math` project,
#   - copy these files into the project's R3/ module directory,
#   - run `lake env lean` on the base, witness, and T1c files.
#
# Optional:
#   --project PATH   use an existing Lake project instead of creating one.
#                    The script copies files into PATH/R3/.
#   --keep           keep the temporary project for inspection.
#
# Environment:
#   R3_LEAN_CACHE_GET=1   run `lake exe cache get` before typechecking.
#   R3_LEAN_TMP=PATH      temp parent directory, default /tmp.

usage() {
  cat <<'EOF'
Usage: verify_lean_sanity.sh [--project PATH] [--keep]

Checks:
  R3/R3Base.lean
  R3/R3_212_Witness.lean
  R3/R3_T1c_40959.lean
  R3/R3_T1c_48895.lean

Set R3_LEAN_CACHE_GET=1 to fetch Mathlib cache before checking.
EOF
}

PROJECT=""
KEEP=0
while [[ $# -gt 0 ]]; do
  case "$1" in
    --project)
      PROJECT="${2:-}"
      if [[ -z "$PROJECT" ]]; then
        echo "missing path after --project" >&2
        exit 2
      fi
      shift 2
      ;;
    --keep)
      KEEP=1
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "unknown argument: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
done

SRC_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if ! command -v lake >/dev/null 2>&1; then
  echo "lake not found on PATH; install Lean/Lake or load the Lean module first" >&2
  exit 127
fi

if ! command -v lean >/dev/null 2>&1; then
  echo "lean not found on PATH; install Lean or load the Lean module first" >&2
  exit 127
fi

TMP_PARENT="${R3_LEAN_TMP:-/tmp}"
TMP_DIR=""

cleanup() {
  if [[ "$KEEP" -eq 0 && -n "$TMP_DIR" && -d "$TMP_DIR" ]]; then
    rm -rf "$TMP_DIR"
  fi
}
trap cleanup EXIT

if [[ -z "$PROJECT" ]]; then
  TMP_DIR="$(mktemp -d "${TMP_PARENT%/}/r3_lean_sanity.XXXXXX")"
  echo "[lean sanity] creating temporary Lake project under $TMP_DIR"
  (cd "$TMP_DIR" && lake new R3 math)
  PROJECT="$TMP_DIR/R3"
else
  PROJECT="$(cd "$PROJECT" && pwd)"
  if [[ ! -f "$PROJECT/lakefile.lean" && ! -f "$PROJECT/lakefile.toml" ]]; then
    echo "--project path is not a Lake project: $PROJECT" >&2
    exit 2
  fi
fi

MODULE_DIR="$PROJECT/R3"
mkdir -p "$MODULE_DIR"
cp "$SRC_DIR/R3Base.lean" "$MODULE_DIR/R3Base.lean"
cp "$SRC_DIR/R3_212_Witness.lean" "$MODULE_DIR/R3_212_Witness.lean"
cp "$SRC_DIR/R3_T1c_40959.lean" "$MODULE_DIR/R3_T1c_40959.lean"
cp "$SRC_DIR/R3_T1c_48895.lean" "$MODULE_DIR/R3_T1c_48895.lean"

echo "[lean sanity] project: $PROJECT"
echo "[lean sanity] lean: $(lean --version)"
echo "[lean sanity] lake: $(lake --version)"

cd "$PROJECT"

if [[ "${R3_LEAN_CACHE_GET:-0}" == "1" ]]; then
  echo "[lean sanity] fetching Mathlib cache"
  lake exe cache get
fi

check_file() {
  local file="$1"
  echo "[lean sanity] checking $file"
  /usr/bin/time -p lake env lean "$file"
}

check_file "R3/R3Base.lean"
check_file "R3/R3_212_Witness.lean"
check_file "R3/R3_T1c_40959.lean"
check_file "R3/R3_T1c_48895.lean"

echo "[lean sanity] all checks completed"
if [[ "$KEEP" -eq 1 ]]; then
  echo "[lean sanity] kept project at $PROJECT"
fi
