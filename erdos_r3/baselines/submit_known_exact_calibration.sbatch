#!/bin/bash
#SBATCH --job-name=r3_exact_cal
#SBATCH --partition=cpu
#SBATCH --account=pi_ergezerm_wit_edu
#SBATCH --time=01:30:00
#SBATCH --array=0-11%12
#SBATCH --cpus-per-task=1
#SBATCH --mem=16G
#SBATCH --output=results/slurm_logs/exact_cal-%A_%a.out
#SBATCH --error=results/slurm_logs/exact_cal-%A_%a.err
#SBATCH --chdir=/work/pi_ergezerm_wit_edu/ergezerm_wit_edu/erdos_r3

# Cheap upper-bound calibration at six known exact values. Cells 0..5 use
# the pure 3-AP/cardinality CNF; cells 6..11 add only lengths 31 and N-1.
# Proofs are discarded. Successful cases are rerun later with archived CNFs,
# proof logging, lower witnesses, drat-trim -L, and cake_lpr.

set -euo pipefail
export PATH=/work/pi_ergezerm_wit_edu/ergezerm_wit_edu-conda/envs/soft/bin:$PATH

R3_DIR=${R3_DIR:-/work/pi_ergezerm_wit_edu/ergezerm_wit_edu/erdos_r3}
cd "$R3_DIR"
mkdir -p results/baselines/known_calibration results/slurm_logs

TASK=${SLURM_ARRAY_TASK_ID:?missing SLURM_ARRAY_TASK_ID}
INDEX=$((TASK % 6))
case $INDEX in
  0) N=100; KNOWN=27 ;;
  1) N=90;  KNOWN=24 ;;
  2) N=80;  KNOWN=22 ;;
  3) N=70;  KNOWN=20 ;;
  4) N=60;  KNOWN=19 ;;
  5) N=50;  KNOWN=16 ;;
  *) exit 2 ;;
esac
TARGET=$((KNOWN + 1))

if [ "$TASK" -lt 6 ]; then
  ARM=pure
  WINDOW_ARGS=(--window-lengths none)
else
  ARM=sparse
  WINDOW_ARGS=(--window-lengths "31,$((N - 1))")
fi

OUTDIR="$R3_DIR/results/baselines/known_calibration/N${N}/${ARM}"
OUT="$OUTDIR/upper_attack.jsonl"
mkdir -p "$OUTDIR" "$OUTDIR/scratch"
if [ -s "$OUT" ]; then
  echo "[skip] $OUT already exists"
  exit 0
fi

KISSAT="$R3_DIR/bin/kissat"
[ -x "$KISSAT" ] || { echo "missing $KISSAT" >&2; exit 1; }
VERSION=$($KISSAT --version | head -1)

BFILE="$OUTDIR/b003002_lt_${N}.txt"
awk -v n="$N" '$1 < n {print}' results/b003002.txt > "$BFILE"
INSTANCE="$OUTDIR/instance.jsonl"
printf '{"chunk_id": %d, "N": %d, "K": %d, "fixed_in": [], "fixed_out": []}\n' \
  "$N" "$N" "$TARGET" > "$INSTANCE"

TMP="$OUT.tmp_${SLURM_JOB_ID}_${TASK}"
set +e
python r3_sat_attack.py \
  --input "$INSTANCE" \
  --N "$N" --K "$TARGET" \
  --window-bounds "$BFILE" \
  "${WINDOW_ARGS[@]}" \
  --array-index 0 \
  --time-limit 3600 \
  --solver-binary "$KISSAT" \
  --solver-label "kissat-exact-${ARM}" \
  --solver-version "$VERSION" \
  --discard-external-proof \
  --work-dir "$OUTDIR/scratch" \
  --output "$TMP"
RC=$?
set -e
mv "$TMP" "$OUT"

if [ "$RC" -ne 0 ] || grep -q '"status": "SAT"' "$OUT"; then
  echo "!!! SAT above recorded exact value: verify immediately" >&2
  scancel "$SLURM_ARRAY_JOB_ID"
  exit 1
fi
