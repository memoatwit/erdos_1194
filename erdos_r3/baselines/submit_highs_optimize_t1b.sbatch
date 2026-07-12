#!/bin/bash
#SBATCH --job-name=r3_highs_opt
#SBATCH --partition=cpu
#SBATCH --account=pi_ergezerm_wit_edu
#SBATCH --time=02:30:00
#SBATCH --array=0-39%20
#SBATCH --cpus-per-task=8
#SBATCH --mem=32G
#SBATCH --output=results/slurm_logs/highs_opt-%A_%a.out
#SBATCH --error=results/slurm_logs/highs_opt-%A_%a.err
#SBATCH --chdir=/work/pi_ergezerm_wit_edu/ergezerm_wit_edu/erdos_r3

# Correct optimization-form HiGHS diagnostic on all 20 T1b chunks.
# Cells 0..19 omit window inequalities; cells 20..39 include them.
# Each task solves the continuous LP relaxation, then the binary MIP maximizing
# sum_i x_i. A valid upper bound below 44 certifies the pinned chunk.

set -euo pipefail
export PATH=/work/pi_ergezerm_wit_edu/ergezerm_wit_edu-conda/envs/soft/bin:$PATH

R3_DIR=${R3_DIR:-/work/pi_ergezerm_wit_edu/ergezerm_wit_edu/erdos_r3}
cd "$R3_DIR"
mkdir -p results/baselines/highs_optimize results/slurm_logs

TASK=$SLURM_ARRAY_TASK_ID
if [ "$TASK" -lt 20 ]; then
  IDX=$TASK
  ARM=offwin
  WINARG=""
else
  IDX=$((TASK - 20))
  ARM=onwin
  WINARG="--windows"
fi

OUT="results/baselines/highs_optimize/highs_opt_${ARM}_idx$(printf '%02d' "$IDX").json"
if [ -s "$OUT" ]; then
  echo "[skip] $OUT already exists"
  exit 0
fi
TMP="$OUT.tmp_${SLURM_JOB_ID}_${TASK}"

set +e
python baselines/r3_highs_optimize.py \
  --input results/N212_K44_broad24_recap300_residual_t1b20.jsonl \
  --array-index "$IDX" \
  --N 212 --target 44 \
  --window-bounds results/b003002.txt \
  $WINARG \
  --lp-time-limit 600 \
  --mip-time-limit 7200 \
  --threads 8 \
  --output "$TMP"
RC=$?
set -e
mv "$TMP" "$OUT"

if [ "$RC" -ne 0 ]; then
  echo "!!! MIP produced a candidate of size at least 44; verify immediately" >&2
  scancel "$SLURM_ARRAY_JOB_ID"
  exit "$RC"
fi
