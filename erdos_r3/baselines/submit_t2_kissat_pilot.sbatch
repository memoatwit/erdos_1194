#!/bin/bash
#SBATCH --job-name=r3_t2_kissat
#SBATCH --partition=cpu
#SBATCH --account=pi_ergezerm_wit_edu
#SBATCH --time=02:30:00
#SBATCH --array=0-99%50
#SBATCH --cpus-per-task=1
#SBATCH --mem=8G
#SBATCH --output=results/slurm_logs/t2_kissat-%A_%a.out
#SBATCH --error=results/slurm_logs/t2_kissat-%A_%a.err
#SBATCH --chdir=/work/pi_ergezerm_wit_edu/ergezerm_wit_edu/erdos_r3
#
# T2 kissat pilot: given that kissat 4.0.4 closed both T1c chunks (the two
# HARDEST audited subproblems) in ~4-5 h each without windows, how much of
# the broad T2 residual does kissat close cheaply?
#
# Design: uniform random 100-chunk sample (seed 42) of the 6,071 T2
# UNKNOWNs, kissat no-window encoding, 2 h per chunk, no proof logging
# (this is a survey, not a certification pass).
#
# Interpretation for the paper:
#   - High close rate (>~90%): the CDCL story strengthens further — the
#     "hard pocket" was largely an artifact of the CP-SAT/CaDiCaL toolchain,
#     and full T2 closure via kissat becomes a realistic follow-up.
#   - Low close rate: T1c really was atypical; the ladder narrative holds.
# Either way the number goes in §4.
#
# Total compute: 100 * 1 core * <=2 h = <=200 CPU-hours.

set -euo pipefail
export PATH=/work/pi_ergezerm_wit_edu/ergezerm_wit_edu-conda/envs/soft/bin:$PATH

R3_DIR="${R3_DIR:-/work/pi_ergezerm_wit_edu/ergezerm_wit_edu/erdos_r3}"
cd "$R3_DIR"
mkdir -p results/baselines/t2_pilot results/baselines/scratch_t2 results/slurm_logs

KISSAT="$R3_DIR/bin/kissat"
if [ ! -x "$KISSAT" ]; then
  echo "kissat binary missing — run: bash baselines/build_kissat.sh" >&2
  exit 1
fi

# Deterministic 100-row sample of the 6,071 broad UNKNOWNs (seed 42).
SAMPLE="results/baselines/t2_pilot/sample100_seed42.jsonl"
if [ ! -s "$SAMPLE" ]; then
  python - "$SAMPLE" <<'PY'
import json, random, sys
rows = [json.loads(l) for l in open("results/N212_K44_window100k_unknowns.jsonl")]
random.seed(42)
sample = random.sample(rows, 100)
with open(sys.argv[1], "w") as fh:
    for r in sorted(sample, key=lambda r: r["chunk_id"]):
        fh.write(json.dumps(r) + "\n")
print(f"wrote {len(sample)} rows")
PY
fi

OUT="results/baselines/t2_pilot/t2_kissat_idx$(printf '%02d' $SLURM_ARRAY_TASK_ID).jsonl"
if [ -s "$OUT" ]; then
  echo "[skip] $OUT already exists"
  exit 0
fi
TMP="$OUT.tmp_${SLURM_JOB_ID}_${SLURM_ARRAY_TASK_ID}"
rm -f "$TMP"

python r3_sat_attack.py \
  --input "$SAMPLE" \
  --N 212 --K 44 \
  --window-bounds results/b003002.txt \
  --window-lengths none \
  --array-index $SLURM_ARRAY_TASK_ID \
  --time-limit 7200 \
  --solver-binary "$KISSAT" \
  --discard-external-proof \
  --work-dir results/baselines/scratch_t2 \
  --output "$TMP"

mv "$TMP" "$OUT"
echo "Done: $OUT"

if grep -q '"status": "SAT"' "$OUT"; then
  echo "!!! SAT row — verify witness with r3_verify.py IMMEDIATELY"
  scancel $SLURM_ARRAY_JOB_ID
fi

# Cleanup survey CNFs to keep scratch small (no proofs are produced).
rm -f results/baselines/scratch_t2/chunk_*_idx${SLURM_ARRAY_TASK_ID}.cnf 2>/dev/null || true
