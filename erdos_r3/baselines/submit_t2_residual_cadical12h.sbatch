#!/bin/bash
#SBATCH --job-name=r3_t2_cad12
#SBATCH --partition=cpu
#SBATCH --account=pi_ergezerm_wit_edu
#SBATCH --time=12:30:00
#SBATCH --array=0-111%50
#SBATCH --cpus-per-task=1
#SBATCH --mem=16G
#SBATCH --output=results/slurm_logs/t2_cad12-%A_%a.out
#SBATCH --error=results/slurm_logs/t2_cad12-%A_%a.err
#SBATCH --chdir=/work/pi_ergezerm_wit_edu/ergezerm_wit_edu/erdos_r3

# Re-attack the 112 UNKNOWN rows from the complete two-hour kissat T2 survey
# with native CaDiCaL 3.0.0 for 12 hours. The deterministic no-window CNF must
# hash identically to the corresponding kissat survey formula.

set -euo pipefail
export PATH=/work/pi_ergezerm_wit_edu/ergezerm_wit_edu-conda/envs/soft/bin:$PATH

R3_DIR=${R3_DIR:-/work/pi_ergezerm_wit_edu/ergezerm_wit_edu/erdos_r3}
cd "$R3_DIR"
mkdir -p results/baselines/t2_residual_cadical12h \
  results/baselines/scratch_t2_residual_cadical12h results/slurm_logs

INPUT="results/baselines/t2_full/residual_unknown112.jsonl"
[ -x "$R3_DIR/bin/cadical-3.0.0" ] || { echo "missing native CaDiCaL" >&2; exit 1; }
[ -x "$R3_DIR/baselines/cadical_kissat_cli_adapter.sh" ] || { echo "missing adapter" >&2; exit 1; }
[ "$(wc -l < "$INPUT")" -eq 112 ] || { echo "expected 112 residual rows" >&2; exit 1; }

IDX=$SLURM_ARRAY_TASK_ID
OUT="results/baselines/t2_residual_cadical12h/cadical_idx$(printf '%03d' "$IDX").jsonl"
if [ -s "$OUT" ]; then
  echo "[skip] $OUT already exists"
  exit 0
fi
TMP="$OUT.tmp_${SLURM_JOB_ID}_${IDX}"
VERSION=$($R3_DIR/bin/cadical-3.0.0 --version | head -1)

set +e
python r3_sat_attack.py \
  --input "$INPUT" \
  --N 212 --K 44 \
  --window-bounds results/b003002.txt \
  --window-lengths none \
  --array-index "$IDX" \
  --time-limit 43200 \
  --solver-binary "$R3_DIR/baselines/cadical_kissat_cli_adapter.sh" \
  --solver-label cadical-3.0.0-no-windows \
  --solver-version "$VERSION" \
  --discard-external-proof \
  --work-dir results/baselines/scratch_t2_residual_cadical12h \
  --output "$TMP"
RC=$?
set -e
mv "$TMP" "$OUT"

if [ "$RC" -ne 0 ] || grep -q '"status": "SAT"' "$OUT"; then
  echo "!!! SAT row: verify the candidate immediately with r3_verify.py" >&2
  scancel "$SLURM_ARRAY_JOB_ID"
  exit 1
fi
