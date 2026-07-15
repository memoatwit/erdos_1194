#!/bin/bash
#SBATCH --job-name=r3_split_ablate
#SBATCH --partition=cpu
#SBATCH --account=pi_ergezerm_wit_edu
#SBATCH --constraint=amd7763
#SBATCH --time=00:15:00
#SBATCH --array=0-499%200
#SBATCH --cpus-per-task=8
#SBATCH --mem=8G
#SBATCH --output=results/slurm_logs/split-ablate-%A_%a.out
#SBATCH --error=results/slurm_logs/split-ablate-%A_%a.err
#SBATCH --chdir=/work/pi_ergezerm_wit_edu/ergezerm_wit_edu/erdos_r3

# Matched ablation of five depth-24 split-variable policies. Each array task
# applies the same uniformly sampled raw 24-bit assignment to all policies,
# sequentially on one node, and rotates policy order by task index.

set -euo pipefail
export PATH=/work/pi_ergezerm_wit_edu/ergezerm_wit_edu-conda/envs/soft/bin:$PATH

R3_DIR=${R3_DIR:-/work/pi_ergezerm_wit_edu/ergezerm_wit_edu/erdos_r3}
cd "$R3_DIR"

OUT_DIR=results/baselines/split_policy_ablation
mkdir -p "$OUT_DIR" results/slurm_logs

IDX=$SLURM_ARRAY_TASK_ID
OUT="$OUT_DIR/split_policy_idx$(printf '%03d' "$IDX").jsonl"
if [[ -s "$OUT" ]]; then
  echo "[skip] $OUT already exists"
  exit 0
fi

TMP="$OUT.tmp_${SLURM_JOB_ID}_${IDX}"
set +e
python baselines/r3_split_policy_ablation.py \
  --sample-index "$IDX" \
  --sample-size 500 \
  --sample-seed 20260715 \
  --policy-seed 1194 \
  --split-count 24 \
  --N 212 --K 44 \
  --time-limit 60 \
  --workers 8 \
  --output "$TMP"
rc=$?
set -e

if [[ -s "$TMP" ]]; then
  mv "$TMP" "$OUT"
fi
if [[ -s "$OUT" ]] && grep -q '"status": "FEASIBLE"' "$OUT"; then
  echo "!!! FEASIBLE row: verify the candidate immediately with r3_verify.py" >&2
  scancel "$SLURM_ARRAY_JOB_ID"
  exit 2
fi
exit "$rc"
