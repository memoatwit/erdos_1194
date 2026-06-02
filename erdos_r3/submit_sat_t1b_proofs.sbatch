#!/bin/bash
#SBATCH --job-name=r3_sat_t1b_proofs
#SBATCH --partition=cpu
#SBATCH --account=pi_ergezerm_wit_edu
#SBATCH --time=06:30:00
#SBATCH --array=0-17%6
#SBATCH --cpus-per-task=1
#SBATCH --mem=32G
#SBATCH --output=results/slurm_logs/sat_t1b_proofs-%A_%a.out
#SBATCH --error=results/slurm_logs/sat_t1b_proofs-%A_%a.err
#
# Proof-producing CDCL/SAT rerun for the 18 T1b chunks that closed UNSAT in
# job 58832970. This uses the same pure 3-AP/cardinality encoding
# (--window-lengths none), but enables PySAT proof logging. On Unity,
# r3_sat_attack.py selects Glucose for pysat:auto when --pysat-with-proof is set
# because the python-sat CaDiCaL backend returns empty proof lists.

set -euo pipefail
export PATH=/work/pi_ergezerm_wit_edu/ergezerm_wit_edu-conda/envs/soft/bin:$PATH

cd "$HOME/erdos_r3"

python -c 'from pysat.card import CardEnc; from pysat.solvers import Solver' 2>/dev/null || \
  python -m pip install --user python-sat 1>&2

INPUT20="$HOME/erdos_r3/results/N212_K44_broad24_recap300_residual_t1b20.jsonl"
INPUT18="$HOME/erdos_r3/results/N212_K44_broad24_recap300_residual_t1b18_unsat.jsonl"
python - <<'PY'
import json
from pathlib import Path

input20 = Path("results/N212_K44_broad24_recap300_residual_t1b20.jsonl")
input18 = Path("results/N212_K44_broad24_recap300_residual_t1b18_unsat.jsonl")
unknown = {40959, 48895}
rows = [json.loads(line) for line in input20.read_text().splitlines() if line.strip()]
selected = [r for r in rows if r.get("chunk_id") not in unknown]
if len(selected) != 18:
    raise SystemExit(f"expected 18 proof rows, got {len(selected)}")
input18.parent.mkdir(parents=True, exist_ok=True)
with input18.open("w") as fh:
    for row in selected:
        fh.write(json.dumps(row) + "\n")
PY

OUT_DIR="$HOME/erdos_r3/results/sat_t1b_proofs"
WORK_DIR="$OUT_DIR/scratch"
mkdir -p "$OUT_DIR" "$WORK_DIR"

OUT="$OUT_DIR/sat_proof_idx$(printf '%02d' "$SLURM_ARRAY_TASK_ID").jsonl"
if [ -s "$OUT" ]; then
  echo "[skip] $OUT already exists"
  exit 0
fi
TMP="$OUT.tmp_${SLURM_JOB_ID}_${SLURM_ARRAY_TASK_ID}"
rm -f "$TMP"

python "$HOME/erdos_r3/r3_sat_attack.py" \
  --input "$INPUT18" \
  --N 212 --K 44 \
  --window-bounds "$HOME/erdos_r3/results/b003002.txt" \
  --window-lengths none \
  --array-index "$SLURM_ARRAY_TASK_ID" \
  --time-limit 21600 \
  --solver-binary pysat:auto \
  --pysat-with-proof \
  --work-dir "$WORK_DIR" \
  --keep-cnf \
  --output "$TMP"

mv "$TMP" "$OUT"
echo "Done: $OUT"

if grep -q '"status": "SAT"' "$OUT"; then
  echo "SAT (= FEASIBLE) found in $OUT — cancelling rest of array."
  scancel "$SLURM_ARRAY_JOB_ID"
fi
