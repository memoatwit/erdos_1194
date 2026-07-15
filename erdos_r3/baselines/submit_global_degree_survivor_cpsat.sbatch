#!/bin/bash
#SBATCH --job-name=r3_gdeg_cp
#SBATCH --partition=cpu
#SBATCH --account=pi_ergezerm_wit_edu
#SBATCH --constraint=amd7763
#SBATCH --time=00:05:00
#SBATCH --array=0-99%100
#SBATCH --cpus-per-task=8
#SBATCH --mem=8G
#SBATCH --output=results/slurm_logs/gdeg-cp-%A_%a.out
#SBATCH --error=results/slurm_logs/gdeg-cp-%A_%a.err
#SBATCH --chdir=/work/pi_ergezerm_wit_edu/ergezerm_wit_edu/erdos_r3

set -euo pipefail
export PATH=/work/pi_ergezerm_wit_edu/ergezerm_wit_edu-conda/envs/soft/bin:$PATH
R3_DIR=${R3_DIR:-/work/pi_ergezerm_wit_edu/ergezerm_wit_edu/erdos_r3}
cd "$R3_DIR"

INPUT=results/global_degree_survivor_sample100.jsonl
OUT_DIR=results/baselines/global_degree_survivor_cpsat
mkdir -p "$OUT_DIR" results/slurm_logs
IDX=$SLURM_ARRAY_TASK_ID
OUT="$OUT_DIR/cpsat_idx$(printf '%03d' "$IDX").jsonl"
[[ -s "$OUT" ]] && exit 0
TMP="$OUT.tmp_${SLURM_JOB_ID}_${IDX}"

set +e
python baselines/r3_cpsat_jsonl_attack.py \
  --input "$INPUT" --array-index "$IDX" \
  --N 212 --K 44 --time-limit 60 --workers 8 \
  --output "$TMP"
rc=$?
set -e
[[ -s "$TMP" ]] && mv "$TMP" "$OUT"
if [[ -s "$OUT" ]] && grep -q '"status": "FEASIBLE"' "$OUT"; then
  echo "!!! FEASIBLE row: verify immediately with r3_verify.py" >&2
  scancel "$SLURM_ARRAY_JOB_ID"
  exit 2
fi
exit "$rc"
