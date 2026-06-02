#!/bin/bash
#SBATCH --job-name=r3_drat_verify4h
#SBATCH --partition=cpu
#SBATCH --account=pi_ergezerm_wit_edu
#SBATCH --time=04:30:00
#SBATCH --array=0-5%6
#SBATCH --cpus-per-task=1
#SBATCH --mem=16G
#SBATCH --output=results/slurm_logs/drat_verify4h-%A_%a.out
#SBATCH --error=results/slurm_logs/drat_verify4h-%A_%a.err
#
# Extended drat-trim verification for the 6 T1b DRAT proofs that timed out
# under the first 1h verifier pass. This does not submit any new solver work;
# it only rechecks already-emitted DRAT proofs with a 4h per-proof cap.

set -euo pipefail
export PATH=/work/pi_ergezerm_wit_edu/ergezerm_wit_edu-conda/envs/soft/bin:$PATH

R3_DIR="${R3_DIR:-/work/pi_ergezerm_wit_edu/ergezerm_wit_edu/erdos_r3}"
cd "$R3_DIR"

if [ ! -x "$R3_DIR/drat-trim" ]; then
  DRAT_TRIM_DIR="$R3_DIR/tools/drat-trim" \
  DRAT_TRIM_BIN="$R3_DIR/drat-trim" \
    bash "$R3_DIR/build_drat_trim.sh" 1>&2
fi

TIMEOUT_CHUNKS=(40943 63231 64319 77311 81279 110587)
CHUNK_ID="${TIMEOUT_CHUNKS[$SLURM_ARRAY_TASK_ID]}"

PROOFS_DIR="$R3_DIR/results/sat_t1b_proofs/scratch"
CNFS_DIR="$R3_DIR/results/sat_t1b_proofs/scratch"
OUT_DIR="$R3_DIR/results/sat_t1b_proofs/verification_shards_4h"
LRAT_DIR="$R3_DIR/results/sat_t1b_proofs/lrat_4h"
mkdir -p "$OUT_DIR" "$LRAT_DIR"

OUT="$OUT_DIR/verify4h_chunk${CHUNK_ID}.jsonl"
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
  --time-limit 14400 \
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
