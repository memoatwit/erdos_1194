#!/bin/bash
#SBATCH --job-name=r3_cdcl_ctrl
#SBATCH --partition=cpu
#SBATCH --account=pi_ergezerm_wit_edu
#SBATCH --time=12:30:00
#SBATCH --array=0-39%20
#SBATCH --cpus-per-task=1
#SBATCH --mem=16G
#SBATCH --output=results/slurm_logs/cdcl_ctrl-%A_%a.out
#SBATCH --error=results/slurm_logs/cdcl_ctrl-%A_%a.err
#SBATCH --chdir=/work/pi_ergezerm_wit_edu/ergezerm_wit_edu/erdos_r3

# Controlled comparison on all 20 T1b chunks:
#   cells 0..19  = native CaDiCaL 3.0.0
#   cells 20..39 = kissat 4.0.4
# Both arms regenerate the exact same deterministic no-window CNF. Output rows
# carry cnf_sha256; hashes for the two arms must match chunk-by-chunk.

set -euo pipefail
export PATH=/work/pi_ergezerm_wit_edu/ergezerm_wit_edu-conda/envs/soft/bin:$PATH

R3_DIR=${R3_DIR:-/work/pi_ergezerm_wit_edu/ergezerm_wit_edu/erdos_r3}
cd "$R3_DIR"
mkdir -p results/baselines/cdcl_controlled results/baselines/scratch_cdcl_controlled results/slurm_logs

INPUT="results/N212_K44_broad24_recap300_residual_t1b20.jsonl"
TASK=$SLURM_ARRAY_TASK_ID
if [ "$TASK" -lt 20 ]; then
  ARM=cadical
  IDX=$TASK
  SOLVER="$R3_DIR/baselines/cadical_kissat_cli_adapter.sh"
  VERSION=$($R3_DIR/bin/cadical-3.0.0 --version | head -1)
else
  ARM=kissat
  IDX=$((TASK - 20))
  SOLVER="$R3_DIR/bin/kissat"
  VERSION=$($SOLVER --version | head -1)
fi

OUT="results/baselines/cdcl_controlled/${ARM}_idx$(printf '%02d' "$IDX").jsonl"
if [ -s "$OUT" ]; then
  echo "[skip] $OUT already exists"
  exit 0
fi
TMP="$OUT.tmp_${SLURM_JOB_ID}_${TASK}"

python r3_sat_attack.py \
  --input "$INPUT" \
  --N 212 --K 44 \
  --window-bounds results/b003002.txt \
  --window-lengths none \
  --array-index "$IDX" \
  --time-limit 43200 \
  --solver-binary "$SOLVER" \
  --solver-label "$ARM-no-windows" \
  --solver-version "$VERSION" \
  --discard-external-proof \
  --work-dir results/baselines/scratch_cdcl_controlled \
  --output "$TMP"

mv "$TMP" "$OUT"
if grep -q '"status": "SAT"' "$OUT"; then
  echo "!!! SAT row: verify the candidate immediately with r3_verify.py" >&2
  scancel "$SLURM_ARRAY_JOB_ID"
  exit 1
fi
