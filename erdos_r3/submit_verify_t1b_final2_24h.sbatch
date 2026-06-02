#!/bin/bash
#SBATCH --job-name=r3_drat_final2
#SBATCH --partition=cpu
#SBATCH --account=pi_ergezerm_wit_edu
#SBATCH --time=24:30:00
#SBATCH --array=0-1%2
#SBATCH --cpus-per-task=1
#SBATCH --mem=32G
#SBATCH --output=results/slurm_logs/drat_final2-%A_%a.out
#SBATCH --error=results/slurm_logs/drat_final2-%A_%a.err
#
# Final certificate-cleanup verifier pass:
#   task 0: chunk 63231, whose 12h pass hit drat-trim's default 40000s cap
#   task 1: chunk 32735, whose 64G proof rerun finally emitted a DRAT proof
#
# This script relies on verify_t1b_proofs.py passing drat-trim -t explicitly
# and using -L for actual LRAT output.

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
  0)
    CHUNK_ID=63231
    PROOFS_DIR="$R3_DIR/results/sat_t1b_proofs/scratch"
    CNFS_DIR="$R3_DIR/results/sat_t1b_proofs/scratch"
    ;;
  1)
    CHUNK_ID=32735
    PROOFS_DIR="$R3_DIR/results/sat_t1b_proof32735_64g/scratch"
    CNFS_DIR="$R3_DIR/results/sat_t1b_proof32735_64g/scratch"
    ;;
  *)
    echo "unexpected array index $SLURM_ARRAY_TASK_ID" >&2
    exit 2
    ;;
esac

OUT_DIR="$R3_DIR/results/sat_t1b_proofs/verification_shards_final2_24h"
LRAT_DIR="$R3_DIR/results/sat_t1b_proofs/lrat_final2_24h"
mkdir -p "$OUT_DIR" "$LRAT_DIR"

OUT="$OUT_DIR/verify24h_chunk${CHUNK_ID}.jsonl"
if [ -s "$OUT" ]; then
  echo "[skip] $OUT already exists"
  exit 0
fi

TMP="$OUT.tmp_${SLURM_JOB_ID}_${SLURM_ARRAY_TASK_ID}"
rm -f "$TMP"

set +e
python "$R3_DIR/verify_t1b_proofs.py" \
  --proofs-dir "$PROOFS_DIR" \
  --cnfs-dir "$CNFS_DIR" \
  --output "$TMP" \
  --drat-trim "$R3_DIR/drat-trim" \
  --chunk-id "$CHUNK_ID" \
  --time-limit 86400 \
  --emit-lrat \
  --lrat-dir "$LRAT_DIR" \
  --exit-zero-on-nonverified
PY_STATUS=$?
set -e

if [ -s "$TMP" ]; then
  mv "$TMP" "$OUT"
else
  python - "$CHUNK_ID" "$PY_STATUS" > "$OUT" <<'PY'
import json, sys, time
chunk_id = int(sys.argv[1])
py_status = int(sys.argv[2])
print(json.dumps({
    "chunk_id": chunk_id,
    "status": "ERROR",
    "error": "verify_t1b_proofs.py produced no JSONL row",
    "python_exit_code": py_status,
    "recorded_at": time.time(),
}))
PY
  rm -f "$TMP"
fi

echo "Done: $OUT"
