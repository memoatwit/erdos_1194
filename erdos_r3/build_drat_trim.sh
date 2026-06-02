#!/bin/bash
# build_drat_trim.sh — fetch and compile drat-trim, the SAT-competition-standard
# DRAT proof verifier. Single-source-file C; builds in seconds.
#
# Output: ./drat-trim (in $HOME/erdos_r3 if invoked from there).
# Idempotent: skips fetch + build if a usable binary already exists.

set -euo pipefail

DEST_DIR="${DRAT_TRIM_DIR:-$HOME/erdos_r3/tools/drat-trim}"
DEST_BIN="${DRAT_TRIM_BIN:-$HOME/erdos_r3/drat-trim}"

if [ -x "$DEST_BIN" ]; then
  echo "[skip] $DEST_BIN already exists"
  "$DEST_BIN" --help 2>&1 | head -3 || true
  exit 0
fi

mkdir -p "$DEST_DIR"
cd "$DEST_DIR"

if [ ! -d .git ]; then
  git clone --depth=1 https://github.com/marijnheule/drat-trim.git .
else
  echo "[info] already a git repo at $DEST_DIR, pulling latest"
  git pull --ff-only || true
fi

# drat-trim is a single .c file; one gcc command.
gcc -O2 -DNDEBUG -o "$DEST_BIN" drat-trim.c

if [ ! -x "$DEST_BIN" ]; then
  echo "[error] build did not produce $DEST_BIN" 1>&2
  exit 1
fi

echo "[done] built $DEST_BIN"
"$DEST_BIN" --help 2>&1 | head -3 || true
