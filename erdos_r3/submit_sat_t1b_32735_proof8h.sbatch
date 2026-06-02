#!/bin/bash
#SBATCH --job-name=r3_sat_32735_p8h
#SBATCH --partition=cpu
#SBATCH --account=pi_ergezerm_wit_edu
#SBATCH --time=08:30:00
#SBATCH --cpus-per-task=1
#SBATCH --mem=32G
#SBATCH --output=results/slurm_logs/sat_32735_p8h-%j.out
#SBATCH --error=results/slurm_logs/sat_32735_p8h-%j.err
#
# Longer proof-producing CDCL rerun for chunk 32735. This chunk closed UNSAT
# in the first pure-CDCL run but timed out under the 6h proof-logging rerun.
# The goal is to emit a nonempty DRAT proof, not to attack T1c.

set -euo pipefail
export PATH=/work/pi_ergezerm_wit_edu/ergezerm_wit_edu-conda/envs/soft/bin:$PATH

cd "$HOME/erdos_r3"

python -c 'from pysat.card import CardEnc; from pysat.solvers import Solver' 2>/dev/null || \
  python -m pip install --user python-sat 1>&2

INPUT="$HOME/erdos_r3/results/N212_K44_broad24_recap300_residual_t1b20.jsonl"
OUT_DIR="$HOME/erdos_r3/results/sat_t1b_proof32735"
WORK_DIR="$OUT_DIR/scratch"
mkdir -p "$OUT_DIR" "$WORK_DIR"

OUT="$OUT_DIR/sat_proof_chunk32735_8h.jsonl"
if [ -s "$OUT" ]; then
  echo "[skip] $OUT already exists"
  exit 0
fi

TMP="$OUT.tmp_${SLURM_JOB_ID}"
rm -f "$TMP"

python "$HOME/erdos_r3/r3_sat_attack.py" \
  --input "$INPUT" \
  --N 212 --K 44 \
  --window-bounds "$HOME/erdos_r3/results/b003002.txt" \
  --window-lengths none \
  --chunk-id 32735 \
  --time-limit 28800 \
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
