#!/bin/bash
#SBATCH --job-name=r3_sat_32735_p64g
#SBATCH --partition=cpu
#SBATCH --account=pi_ergezerm_wit_edu
#SBATCH --time=12:30:00
#SBATCH --cpus-per-task=1
#SBATCH --mem=64G
#SBATCH --output=results/slurm_logs/sat_32735_p64g-%j.out
#SBATCH --error=results/slurm_logs/sat_32735_p64g-%j.err
#
# Larger-memory proof-producing CDCL rerun for chunk 32735. This chunk closed
# UNSAT in the first pure-CDCL run, timed out under the first proof-logging
# rerun, and then OOM'd with 32G. This job keeps the same pure 3-AP encoding
# but raises memory to 64G and wall to 12h.

set -euo pipefail
export PATH=/work/pi_ergezerm_wit_edu/ergezerm_wit_edu-conda/envs/soft/bin:$PATH

R3_DIR="${R3_DIR:-/work/pi_ergezerm_wit_edu/ergezerm_wit_edu/erdos_r3}"
cd "$R3_DIR"

python -c 'from pysat.card import CardEnc; from pysat.solvers import Solver' 2>/dev/null || \
  python -m pip install --user python-sat 1>&2

INPUT="$R3_DIR/results/N212_K44_broad24_recap300_residual_t1b20.jsonl"
OUT_DIR="$R3_DIR/results/sat_t1b_proof32735_64g"
WORK_DIR="$OUT_DIR/scratch"
mkdir -p "$OUT_DIR" "$WORK_DIR"

OUT="$OUT_DIR/sat_proof_chunk32735_12h64g.jsonl"
if [ -s "$OUT" ]; then
  echo "[skip] $OUT already exists"
  exit 0
fi

TMP="$OUT.tmp_${SLURM_JOB_ID}"
rm -f "$TMP"

python "$R3_DIR/r3_sat_attack.py" \
  --input "$INPUT" \
  --N 212 --K 44 \
  --window-bounds "$R3_DIR/results/b003002.txt" \
  --window-lengths none \
  --chunk-id 32735 \
  --time-limit 43200 \
  --solver-binary pysat:auto \
  --pysat-with-proof \
  --work-dir "$WORK_DIR" \
  --keep-cnf \
  --output "$TMP"

mv "$TMP" "$OUT"
echo "Done: $OUT"

if grep -q '"status": "SAT"' "$OUT"; then
  echo "SAT (= FEASIBLE) found in $OUT. Verify immediately with r3_verify.py."
fi
