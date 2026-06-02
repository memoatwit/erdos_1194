#!/bin/bash
#SBATCH --job-name=r3_sat_t1c_diag
#SBATCH --partition=cpu
#SBATCH --account=pi_ergezerm_wit_edu
#SBATCH --time=12:30:00
#SBATCH --array=0-3%4
#SBATCH --cpus-per-task=1
#SBATCH --mem=32G
#SBATCH --output=results/slurm_logs/sat_t1c_diag-%A_%a.out
#SBATCH --error=results/slurm_logs/sat_t1c_diag-%A_%a.err
#
# Two-arm diagnostic for the current T1c hard core {40959, 48895}.
#
#   tasks 0,1: pure 3-AP/cardinality encoding, 12h cap
#   tasks 2,3: window-length subset L in {31,100,199}, totalizer windows, 4h cap
#
# This is diagnostic, not proof-producing; if either arm closes a T1c chunk,
# rerun that closure later with proof logging.

set -euo pipefail
export PATH=/work/pi_ergezerm_wit_edu/ergezerm_wit_edu-conda/envs/soft/bin:$PATH

cd "$HOME/erdos_r3"

python -c 'from pysat.card import CardEnc; from pysat.solvers import Solver' 2>/dev/null || \
  python -m pip install --user python-sat 1>&2

INPUT20="$HOME/erdos_r3/results/N212_K44_broad24_recap300_residual_t1b20.jsonl"
INPUT2="$HOME/erdos_r3/results/N212_K44_broad24_recap300_residual_t1c2.jsonl"
python - <<'PY'
import json
from pathlib import Path

input20 = Path("results/N212_K44_broad24_recap300_residual_t1b20.jsonl")
input2 = Path("results/N212_K44_broad24_recap300_residual_t1c2.jsonl")
t1c = {40959, 48895}
rows = [json.loads(line) for line in input20.read_text().splitlines() if line.strip()]
selected = [r for r in rows if r.get("chunk_id") in t1c]
if len(selected) != 2:
    raise SystemExit(f"expected 2 T1c rows, got {len(selected)}")
input2.parent.mkdir(parents=True, exist_ok=True)
with input2.open("w") as fh:
    for row in selected:
        fh.write(json.dumps(row) + "\n")
PY

TASK="$SLURM_ARRAY_TASK_ID"
if [ "$TASK" -lt 2 ]; then
  ARM="pure12h"
  ROW_IDX="$TASK"
  WINDOW_LENGTHS="none"
  TIME_LIMIT=43200
  unset R3_SAT_WINDOW_ENC || true
else
  ARM="win31_100_199_4h"
  ROW_IDX=$((TASK - 2))
  WINDOW_LENGTHS="31,100,199"
  TIME_LIMIT=14400
  export R3_SAT_WINDOW_ENC=totalizer
fi

OUT_DIR="$HOME/erdos_r3/results/sat_t1c_diag"
WORK_DIR="$OUT_DIR/scratch_${ARM}"
mkdir -p "$OUT_DIR" "$WORK_DIR"

OUT="$OUT_DIR/sat_t1c_${ARM}_idx$(printf '%02d' "$ROW_IDX").jsonl"
if [ -s "$OUT" ]; then
  echo "[skip] $OUT already exists"
  exit 0
fi
TMP="$OUT.tmp_${SLURM_JOB_ID}_${SLURM_ARRAY_TASK_ID}"
rm -f "$TMP"

python "$HOME/erdos_r3/r3_sat_attack.py" \
  --input "$INPUT2" \
  --N 212 --K 44 \
  --window-bounds "$HOME/erdos_r3/results/b003002.txt" \
  --window-lengths "$WINDOW_LENGTHS" \
  --array-index "$ROW_IDX" \
  --time-limit "$TIME_LIMIT" \
  --solver-binary pysat:auto \
  --work-dir "$WORK_DIR" \
  --output "$TMP"

mv "$TMP" "$OUT"
echo "Done: $OUT"

if grep -q '"status": "SAT"' "$OUT"; then
  echo "SAT (= FEASIBLE) found in $OUT — cancelling rest of array."
  scancel "$SLURM_ARRAY_JOB_ID"
fi

