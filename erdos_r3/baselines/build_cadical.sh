#!/bin/bash
# Build the pinned native CaDiCaL release used by the controlled comparison.
set -euo pipefail

R3_DIR=${R3_DIR:-/work/pi_ergezerm_wit_edu/ergezerm_wit_edu/erdos_r3}
TAG=${CADICAL_TAG:-rel-3.0.0}
SRC="$R3_DIR/third_party/cadical-$TAG"
BIN="$R3_DIR/bin/cadical-3.0.0"
mkdir -p "$R3_DIR/third_party" "$R3_DIR/bin"

if [ ! -d "$SRC/.git" ]; then
  git clone --depth 1 --branch "$TAG" https://github.com/arminbiere/cadical.git "$SRC"
fi
cd "$SRC"
./configure
make -j4
cp build/cadical "$BIN"
"$BIN" --version
echo "cadical installed at $BIN"
