#!/bin/bash
# build_kissat.sh — build a current kissat binary into $R3_DIR/bin/.
# Run once on a Unity login node (takes ~2 minutes):
#   bash baselines/build_kissat.sh
set -euo pipefail

R3_DIR=${R3_DIR:-/work/pi_ergezerm_wit_edu/ergezerm_wit_edu/erdos_r3}
SRC="$R3_DIR/third_party/kissat"
mkdir -p "$R3_DIR/third_party" "$R3_DIR/bin"

if [ ! -d "$SRC" ]; then
  git clone --depth 1 https://github.com/arminbiere/kissat.git "$SRC"
fi
cd "$SRC"
./configure
make -j4
cp build/kissat "$R3_DIR/bin/kissat"
"$R3_DIR/bin/kissat" --version
echo "kissat installed at $R3_DIR/bin/kissat"
