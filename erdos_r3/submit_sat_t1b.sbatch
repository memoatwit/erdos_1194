#!/bin/bash
#SBATCH --job-name=r3_sat_t1b
#SBATCH --partition=cpu
#SBATCH --account=pi_ergezerm_wit_edu
#SBATCH --time=04:30:00
#SBATCH --array=0-19%20
#SBATCH --cpus-per-task=1
#SBATCH --mem=16G
#SBATCH --output=results/slurm_logs/sat_t1b-%A_%a.out
#SBATCH --error=results/slurm_logs/sat_t1b-%A_%a.err
#
# CDCL/SAT attack on the 20 T1b chunks from the full-T1 HiGHS longwall audit
# (job 58782313). One SLURM task per chunk, single-threaded (CDCL is
# typically not parallelized at this stage). This first pass intentionally uses
# the pure 3-AP/cardinality encoding (no OEIS window constraints) to test CDCL
# as a genuinely different paradigm from the CP-SAT/MIP window-bound runs.
#
# Per-task wall: 4 hours solver cap + 30 min headroom = 4.5h SBATCH time.
# Total compute: 20 tasks * 1 core * 4h = 80 CPU-hours.

set -euo pipefail
export PATH=/work/pi_ergezerm_wit_edu/ergezerm_wit_edu-conda/envs/soft/bin:$PATH

cd $HOME/erdos_r3

# Make sure PySAT is importable. The cardinality encodings live in pysat.card.
python -c 'from pysat.card import CardEnc' 2>/dev/null || \
  python -m pip install --user python-sat 1>&2

# Use the bundled PySAT backend so the job does not depend on a site-installed
# Kissat/CaDiCaL binary. The r3_sat_attack.py 'pysat:auto' selector prefers
# CaDiCaL if available, then Glucose/MiniSat fallbacks.
python - <<'PY' 1>&2
from pysat.solvers import Solver
for name in ("cadical195", "cadical153", "cadical103", "glucose4", "glucose3", "minisat22"):
    try:
        with Solver(name=name):
            print(f"[setup] usable PySAT solver: {name}")
            break
    except Exception:
        pass
else:
    raise SystemExit("no usable PySAT solver found")
PY

# Ensure the T1b residual file exists. If not, build it from the residual45.
INPUT="$HOME/erdos_r3/results/N212_K44_broad24_recap300_residual_t1b20.jsonl"
if [ ! -s "$INPUT" ]; then
  python "$HOME/erdos_r3/extract_t1b_residual20.py" \
    --input "$HOME/erdos_r3/results/N212_K44_broad24_recap300_residual45.jsonl" \
    --output "$INPUT"
fi

OUT_DIR="$HOME/erdos_r3/results/sat_t1b"
WORK_DIR="$HOME/erdos_r3/results/sat_t1b/scratch"
mkdir -p "$OUT_DIR" "$WORK_DIR"

OUT="$OUT_DIR/sat_attack_idx$(printf '%02d' $SLURM_ARRAY_TASK_ID).jsonl"
if [ -s "$OUT" ]; then
  echo "[skip] $OUT already exists"
  exit 0
fi
TMP="$OUT.tmp_${SLURM_JOB_ID}_${SLURM_ARRAY_TASK_ID}"
rm -f "$TMP"

python "$HOME/erdos_r3/r3_sat_attack.py" \
  --input "$INPUT" \
  --N 212 --K 44 \
  --window-bounds "$HOME/erdos_r3/results/b003002.txt" \
  --window-lengths none \
  --array-index $SLURM_ARRAY_TASK_ID \
  --time-limit 14400 \
  --solver-binary pysat:auto \
  --work-dir "$WORK_DIR" \
  --output "$TMP"

mv "$TMP" "$OUT"
echo "Done: $OUT"

# Stop the whole array if any SAT (FEASIBLE) row appears.
if grep -q '"status": "SAT"' "$OUT"; then
  echo "SAT (= FEASIBLE) found in $OUT — cancelling rest of array."
  scancel $SLURM_ARRAY_JOB_ID
fi
