#!/bin/bash
#SBATCH --job-name=r3_gdeg_ks
#SBATCH --partition=cpu
#SBATCH --account=pi_ergezerm_wit_edu
#SBATCH --constraint=amd7763
#SBATCH --time=02:15:00
#SBATCH --array=0-99%100
#SBATCH --cpus-per-task=1
#SBATCH --mem=8G
#SBATCH --output=results/slurm_logs/gdeg-ks-%A_%a.out
#SBATCH --error=results/slurm_logs/gdeg-ks-%A_%a.err
#SBATCH --chdir=/work/pi_ergezerm_wit_edu/ergezerm_wit_edu/erdos_r3

set -euo pipefail
export PATH=/work/pi_ergezerm_wit_edu/ergezerm_wit_edu-conda/envs/soft/bin:$PATH
R3_DIR=${R3_DIR:-/work/pi_ergezerm_wit_edu/ergezerm_wit_edu/erdos_r3}
cd "$R3_DIR"

INPUT=results/global_degree_survivor_sample100.jsonl
OUT_DIR=results/baselines/global_degree_survivor_kissat
WORK_DIR=/scratch4/workspace/ergezerm_wit_edu-soft_speech/r3_global_degree_kissat
mkdir -p "$OUT_DIR" "$WORK_DIR" results/slurm_logs
IDX=$SLURM_ARRAY_TASK_ID
OUT="$OUT_DIR/kissat_idx$(printf '%03d' "$IDX").jsonl"
[[ -s "$OUT" ]] && exit 0
TMP="$OUT.tmp_${SLURM_JOB_ID}_${IDX}"

set +e
python r3_sat_attack.py \
  --input "$INPUT" --array-index "$IDX" \
  --N 212 --K 44 \
  --window-bounds results/b003002.txt --window-lengths none \
  --time-limit 7200 \
  --solver-binary "$R3_DIR/bin/kissat" \
  --solver-label "kissat-global-degree-survivor" \
  --solver-version "$("$R3_DIR/bin/kissat" --version | head -1)" \
  --discard-external-proof \
  --work-dir "$WORK_DIR" \
  --output "$TMP"
rc=$?
set -e
[[ -s "$TMP" ]] && mv "$TMP" "$OUT"
if [[ -s "$OUT" ]] && grep -q '"status": "SAT"' "$OUT"; then
  echo "!!! SAT row: verify immediately with r3_verify.py" >&2
  scancel "$SLURM_ARRAY_JOB_ID"
  exit 2
fi
exit "$rc"
