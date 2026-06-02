#!/bin/bash
#SBATCH --job-name=r3_highs_45
#SBATCH --partition=cpu
#SBATCH --account=pi_ergezerm_wit_edu
#SBATCH --time=01:30:00
#SBATCH --array=0-44%30
#SBATCH --cpus-per-task=8
#SBATCH --mem=8G
#SBATCH --output=results/slurm_logs/highs45-%A_%a.out
#SBATCH --error=results/slurm_logs/highs45-%A_%a.err
#
# HiGHS MIP attack on the 45 surviving recap300 UNKNOWN chunks.
# One SLURM task per chunk; each task is an isolated Python process so
# highspy state cannot leak between chunks.
#
# Per-task wall: 1 hour MIP cap + 30 min headroom = 1.5h SBATCH time.
# Total compute: 45 tasks * 8 cores * 1h = 360 CPU-hours.

set -euo pipefail
export PATH=/work/pi_ergezerm_wit_edu/ergezerm_wit_edu-conda/envs/soft/bin:$PATH

cd $HOME/erdos_r3

# Ensure highspy is installed in the soft env (one-time; harmless if already).
python -c 'import highspy' 2>/dev/null || \
  python -m pip install --user highspy 1>&2

INPUT="$HOME/erdos_r3/results/N212_K44_broad24_recap300_sample100.jsonl"
OUT_DIR="$HOME/erdos_r3/results/highs45"
mkdir -p "$OUT_DIR"

OUT="$OUT_DIR/highs_attack_idx$(printf '%02d' $SLURM_ARRAY_TASK_ID).jsonl"
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
  --array-index $SLURM_ARRAY_TASK_ID \
  --time-limit 3600 \
  --threads 8 \
  --output "$TMP"

mv "$TMP" "$OUT"
echo "Done: $OUT"

# Stop the whole array if any FEASIBLE row appears.
if grep -q '"status": "FEASIBLE"' "$OUT"; then
  echo "FEASIBLE found in $OUT — cancelling rest of array."
  scancel $SLURM_ARRAY_JOB_ID
fi
