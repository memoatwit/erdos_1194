#!/bin/bash
#SBATCH --job-name=r3_drat_t1c
#SBATCH --partition=cpu
#SBATCH --account=pi_ergezerm_wit_edu
#SBATCH --time=48:30:00
#SBATCH --array=0-1
#SBATCH --cpus-per-task=1
#SBATCH --mem=64G
#SBATCH --output=results/slurm_logs/drat_t1c-%A_%a.out
#SBATCH --error=results/slurm_logs/drat_t1c-%A_%a.err
#SBATCH --chdir=/work/pi_ergezerm_wit_edu/ergezerm_wit_edu/erdos_r3
#
# Independent DRAT verification of the two kissat UNSAT proofs that closed
# T1c (job 61424632, no-window encoding):
#   task 0: chunk 40959 — proof ~17.4 GB, solve time 14,204.9 s
#   task 1: chunk 48895 — proof ~14.3 GB, solve time 17,621.7 s
#
# THE PAPER'S NEW HEADLINE DEPENDS ON THIS PASS. Until drat-trim says
# VERIFIED, the claim is "kissat reports UNSAT", not "certified close".
#
# Sizing: the previous T1b verifications took 49,758 s and 80,961 s on
# proofs of similar-or-smaller size, so 48 h + 64 G is deliberate headroom.
# drat-trim's default internal cap is 40,000 s — verify_t1b_proofs.py must
# pass -t explicitly (it does, via --time-limit).

set -euo pipefail
export PATH=/work/pi_ergezerm_wit_edu/ergezerm_wit_edu-conda/envs/soft/bin:$PATH

R3_DIR="${R3_DIR:-/work/pi_ergezerm_wit_edu/ergezerm_wit_edu/erdos_r3}"
cd "$R3_DIR"

if [ ! -x "$R3_DIR/drat-trim" ]; then
  DRAT_TRIM_DIR="$R3_DIR/tools/drat-trim" \
  DRAT_TRIM_BIN="$R3_DIR/drat-trim" \
    bash "$R3_DIR/build_drat_trim.sh" 1>&2
fi

case "$SLURM_ARRAY_TASK_ID" in
  0) CHUNK_ID=40959 ;;
  1) CHUNK_ID=48895 ;;
  *) echo "unexpected array index $SLURM_ARRAY_TASK_ID" >&2; exit 2 ;;
esac

SCRATCH="$R3_DIR/results/baselines/scratch_t1c"

# Guard: both the proof and the matching CNF must exist (the CNF is what the
# proof refutes — verification is meaningless without the exact formula).
PROOF="$SCRATCH/chunk_$(printf '%08d' $CHUNK_ID).drat"
CNF="$SCRATCH/chunk_$(printf '%08d' $CHUNK_ID).cnf"
for f in "$PROOF" "$CNF"; do
  if [ ! -s "$f" ]; then
    echo "MISSING: $f — locate the artifact before verifying" >&2
    exit 1
  fi
done

OUT_DIR="$R3_DIR/results/baselines/t1c_verification"
LRAT_DIR="$R3_DIR/results/baselines/t1c_lrat"
mkdir -p "$OUT_DIR" "$LRAT_DIR"

OUT="$OUT_DIR/verify48h_chunk${CHUNK_ID}.jsonl"
if [ -s "$OUT" ]; then
  echo "[skip] $OUT already exists"
  exit 0
fi
TMP="$OUT.tmp_${SLURM_JOB_ID}_${SLURM_ARRAY_TASK_ID}"
rm -f "$TMP"

set +e
python "$R3_DIR/verify_t1b_proofs.py" \
  --proofs-dir "$SCRATCH" \
  --cnfs-dir "$SCRATCH" \
  --output "$TMP" \
  --drat-trim "$R3_DIR/drat-trim" \
  --chunk-id "$CHUNK_ID" \
  --time-limit 172000 \
  --emit-lrat \
  --lrat-dir "$LRAT_DIR" \
  --exit-zero-on-nonverified
PY_STATUS=$?
set -e

if [ -s "$TMP" ]; then
  mv "$TMP" "$OUT"
else
  echo "{\"chunk_id\": $CHUNK_ID, \"status\": \"VERIFIER_ERROR\", \"exit\": $PY_STATUS}" > "$OUT"
fi

echo "Done: $OUT"
grep -o '"status": "[A-Z_]*"' "$OUT" || true
