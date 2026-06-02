#!/bin/bash
#SBATCH --job-name=r3_highs_t1_full8h
#SBATCH --partition=cpu
#SBATCH --account=pi_ergezerm_wit_edu
#SBATCH --time=08:45:00
#SBATCH --array=0-44%30
#SBATCH --cpus-per-task=8
#SBATCH --mem=8G
#SBATCH --output=results/slurm_logs/highs_t1_full8h-%A_%a.out
#SBATCH --error=results/slurm_logs/highs_t1_full8h-%A_%a.err
#
# Full T1 long-wall HiGHS run.
#
# Runs all 45 rows of results/N212_K44_broad24_recap300_residual45.jsonl with
# an 8h MIP cap.  This is intentionally NOT submitted automatically; use it
# only if we decide to audit the provisional T1a/T1b split.

set -euo pipefail
export PATH=/work/pi_ergezerm_wit_edu/ergezerm_wit_edu-conda/envs/soft/bin:$PATH

cd "$HOME/erdos_r3"

python -c 'import highspy' 2>/dev/null || \
  python -m pip install --user highspy 1>&2

INPUT="$HOME/erdos_r3/results/N212_K44_broad24_recap300_residual45.jsonl"
OUT_DIR="$HOME/erdos_r3/results/highs_t1_longwall45"
mkdir -p "$OUT_DIR"

ROW_INDEX="$SLURM_ARRAY_TASK_ID"
OUT="$OUT_DIR/highs_longwall_row$(printf '%02d' "$ROW_INDEX").jsonl"

if [ -s "$OUT" ]; then
  echo "[skip] $OUT already exists"
  exit 0
fi

TMP="$OUT.tmp_${SLURM_JOB_ID}_${SLURM_ARRAY_TASK_ID}"
rm -f "$TMP"

python "$HOME/erdos_r3/r3_highs_attack.py" \
  --input "$INPUT" \
  --status UNKNOWN \
  --N 212 --K 44 \
  --window-bounds "$HOME/erdos_r3/results/b003002.txt" \
  --witness-hint "$HOME/erdos_r3/results/N212_K43_witness.json" \
  --array-index "$ROW_INDEX" \
  --time-limit 28800 \
  --threads 8 \
  --log \
  --mip-report-level 2 \
  --log-dev-level 1 \
  --mip-min-logging-interval 60 \
  --output "$TMP"

mv "$TMP" "$OUT"
echo "Done: $OUT"

if grep -q '"status": "FEASIBLE"' "$OUT"; then
  echo "FEASIBLE found in $OUT — cancelling rest of array."
  scancel "$SLURM_ARRAY_JOB_ID"
fi
