#!/usr/bin/env bash

# Build the formally verified cake_lpr LRAT/LPR checker from a pinned source
# revision. The repository ships CakeML-generated assembly; building the
# executable only requires a C compiler and does not rebuild the HOL4 proof.

set -euo pipefail

R3_DIR=${R3_DIR:-/work/pi_ergezerm_wit_edu/ergezerm_wit_edu/erdos_r3}
SOURCE_DIR=${CAKE_LPR_SOURCE_DIR:-$R3_DIR/tools/cake_lpr}
TARGET=${CAKE_LPR_BIN:-$R3_DIR/bin/cake_lpr}
REPOSITORY=https://github.com/tanyongkiam/cake_lpr.git
COMMIT=a4323b203cc9ecd584ba7da9e3fff08135a09d5f

mkdir -p "$(dirname "$SOURCE_DIR")" "$(dirname "$TARGET")"

if [ ! -d "$SOURCE_DIR/.git" ]; then
  git clone "$REPOSITORY" "$SOURCE_DIR"
fi

if ! git -C "$SOURCE_DIR" cat-file -e "$COMMIT^{commit}" 2>/dev/null; then
  git -C "$SOURCE_DIR" fetch --depth 1 origin "$COMMIT"
fi
git -C "$SOURCE_DIR" checkout --detach "$COMMIT"

make -C "$SOURCE_DIR" cake_lpr
install -m 0755 "$SOURCE_DIR/cake_lpr" "$TARGET"

{
  printf 'repository=%s\n' "$REPOSITORY"
  printf 'commit=%s\n' "$COMMIT"
  printf 'sha256='
  sha256sum "$TARGET" | awk '{print $1}'
} > "$TARGET.provenance"

"$TARGET" "$SOURCE_DIR/example.cnf" "$SOURCE_DIR/example.lpr" \
  | grep -q 's VERIFIED UNSAT'

echo "cake_lpr ready: $TARGET"
cat "$TARGET.provenance"
