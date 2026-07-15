#!/bin/bash
#SBATCH --job-name=r3_gdeg_cert6
#SBATCH --partition=cpu
#SBATCH --account=pi_ergezerm_wit_edu
#SBATCH --time=72:30:00
#SBATCH --array=0-5%6
#SBATCH --cpus-per-task=1
#SBATCH --mem=64G
#SBATCH --output=results/slurm_logs/gdeg_cert6-%A_%a.out
#SBATCH --error=results/slurm_logs/gdeg_cert6-%A_%a.err
#SBATCH --chdir=/work/pi_ergezerm_wit_edu/ergezerm_wit_edu/erdos_r3

set -euo pipefail
export PATH=/work/pi_ergezerm_wit_edu/ergezerm_wit_edu-conda/envs/soft/bin:$PATH

R3_DIR=${R3_DIR:-/work/pi_ergezerm_wit_edu/ergezerm_wit_edu/erdos_r3}
cd "$R3_DIR"
mkdir -p results/baselines/global_degree_cert_sample6 results/slurm_logs

INDEX=${SLURM_ARRAY_TASK_ID:?missing SLURM_ARRAY_TASK_ID}
INPUT=results/global_degree_cert_sample6.jsonl
CHUNK_ID=$(python - "$INPUT" "$INDEX" <<'PY'
import json, sys
rows = [json.loads(line) for line in open(sys.argv[1]) if line.strip()]
print(rows[int(sys.argv[2])]["chunk_id"])
PY
)

case $((INDEX % 2)) in
  0) SCRATCH_ROOT=/scratch4/workspace/ergezerm_wit_edu-soft_speech ;;
  1) SCRATCH_ROOT=/scratch3/workspace/ergezerm_wit_edu-superfund ;;
esac
SCRATCH="$SCRATCH_ROOT/r3_global_degree_cert_sample6/chunk_${CHUNK_ID}"
OUTDIR="$R3_DIR/results/baselines/global_degree_cert_sample6/chunk_${CHUNK_ID}"
FINAL="$OUTDIR/provenance.json"
mkdir -p "$SCRATCH" "$OUTDIR"

if [ -s "$FINAL" ] && grep -q '"cake_lpr_status": "VERIFIED"' "$FINAL"; then
  echo "[skip] already verified: $FINAL"
  exit 0
fi

KISSAT="$R3_DIR/bin/kissat"
DRATTRIM="$R3_DIR/drat-trim"
CAKELPR="$R3_DIR/bin/cake_lpr"
[ -x "$KISSAT" ] || { echo "missing $KISSAT" >&2; exit 1; }
[ -x "$DRATTRIM" ] || { echo "missing $DRATTRIM" >&2; exit 1; }
[ -x "$CAKELPR" ] || { echo "missing $CAKELPR" >&2; exit 1; }

ATTACK="$SCRATCH/attack.jsonl"
if [ ! -s "$ATTACK" ]; then
  python r3_sat_attack.py \
    --input "$INPUT" \
    --N 212 --K 44 \
    --window-bounds results/b003002.txt \
    --window-lengths none \
    --array-index "$INDEX" \
    --time-limit 21600 \
    --solver-binary "$KISSAT" \
    --solver-label kissat-global-degree-certified-sample \
    --solver-version "$($KISSAT --version | head -1)" \
    --keep-cnf \
    --work-dir "$SCRATCH" \
    --output "$ATTACK" \
    > "$SCRATCH/attack_driver.log" 2>&1
fi

read -r STATUS PRIOR_HASH ACTUAL_HASH < <(python - "$INPUT" "$INDEX" "$ATTACK" <<'PY'
import json, sys
selected = [json.loads(line) for line in open(sys.argv[1]) if line.strip()][int(sys.argv[2])]
attack = [json.loads(line) for line in open(sys.argv[3]) if line.strip()][-1]
print(attack.get("status", "MISSING"), selected["prior_cnf_sha256"], attack.get("cnf_sha256", ""))
PY
)
if [ "$STATUS" = SAT ]; then
  echo "!!! SAT candidate on chunk $CHUNK_ID; verify with r3_verify.py" >&2
  scancel "$SLURM_ARRAY_JOB_ID"
  exit 3
fi
[ "$STATUS" = UNSAT ] || { echo "proof rerun did not close: $STATUS" >&2; exit 4; }
[ "$PRIOR_HASH" = "$ACTUAL_HASH" ] || {
  echo "CNF drift: prior=$PRIOR_HASH actual=$ACTUAL_HASH" >&2
  exit 5
}

PADDED=$(printf '%08d' "$CHUNK_ID")
CNF="$SCRATCH/chunk_${PADDED}.cnf"
DRAT="$SCRATCH/chunk_${PADDED}.drat"
LRAT="$SCRATCH/chunk_${PADDED}.lrat"
[ -s "$CNF" ] || { echo "missing $CNF" >&2; exit 6; }
[ -s "$DRAT" ] || { echo "missing $DRAT" >&2; exit 6; }

DTRIM_LOG="$SCRATCH/drat-trim.log"
DTRIM_SECONDS="$SCRATCH/drat-trim.seconds"
if [ ! -s "$LRAT" ] || ! grep -q 's VERIFIED' "$DTRIM_LOG" 2>/dev/null; then
  START=$(date +%s)
  set +e
  "$DRATTRIM" "$CNF" "$DRAT" -t 120000 -L "$LRAT" > "$DTRIM_LOG" 2>&1
  DTRIM_RC=$?
  set -e
  echo $(($(date +%s) - START)) > "$DTRIM_SECONDS"
  [ "$DTRIM_RC" -eq 0 ] || true
fi
grep -q 's VERIFIED' "$DTRIM_LOG" || { echo "drat-trim did not verify" >&2; exit 7; }
[ -s "$LRAT" ] || { echo "drat-trim emitted no LRAT" >&2; exit 7; }

CAKE_LOG="$SCRATCH/cake_lpr.log"
CAKE_SECONDS="$SCRATCH/cake_lpr.seconds"
export CML_HEAP_SIZE=${CML_HEAP_SIZE:-24000}
export CML_STACK_SIZE=${CML_STACK_SIZE:-24000}
if ! grep -q 's VERIFIED UNSAT' "$CAKE_LOG" 2>/dev/null; then
  START=$(date +%s)
  set +e
  timeout --signal=TERM 86400 "$CAKELPR" "$CNF" "$LRAT" > "$CAKE_LOG" 2>&1
  CAKE_RC=$?
  set -e
  echo $(($(date +%s) - START)) > "$CAKE_SECONDS"
  [ "$CAKE_RC" -eq 0 ] || true
fi
grep -q 's VERIFIED UNSAT' "$CAKE_LOG" || { echo "cake_lpr did not verify" >&2; exit 8; }

sha256sum "$CNF" "$DRAT" "$LRAT" > "$SCRATCH/SHA256SUMS"
python - "$FINAL" "$INPUT" "$INDEX" "$ATTACK" "$CNF" "$DRAT" "$LRAT" \
  "$DTRIM_SECONDS" "$CAKE_SECONDS" <<PY
import hashlib, json, pathlib, subprocess, sys

def sha(path):
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for block in iter(lambda: handle.read(1 << 22), b""):
            digest.update(block)
    return digest.hexdigest()

def seconds(path):
    p = pathlib.Path(path)
    return int(p.read_text().strip()) if p.is_file() else None

final, input_path, index, attack_path, cnf, drat, lrat, dtrim_s, cake_s = sys.argv[1:]
selected = [json.loads(line) for line in open(input_path) if line.strip()][int(index)]
attack = [json.loads(line) for line in open(attack_path) if line.strip()][-1]
payload = {
    "chunk_id": selected["chunk_id"],
    "selection_quantile": selected["selection_quantile"],
    "selection_rank": selected["selection_rank"],
    "prior_solver_seconds": selected["prior_solver_seconds"],
    "prior_cnf_sha256": selected["prior_cnf_sha256"],
    "status": attack["status"],
    "proof_solver_seconds": attack.get("solver_seconds"),
    "cnf_sha256": sha(cnf),
    "cnf_hash_matches_survey": sha(cnf) == selected["prior_cnf_sha256"],
    "drat_sha256": sha(drat),
    "lrat_sha256": sha(lrat),
    "cnf_bytes": pathlib.Path(cnf).stat().st_size,
    "drat_bytes": pathlib.Path(drat).stat().st_size,
    "lrat_bytes": pathlib.Path(lrat).stat().st_size,
    "drat_trim_status": "VERIFIED",
    "drat_trim_seconds": seconds(dtrim_s),
    "cake_lpr_status": "VERIFIED",
    "cake_lpr_seconds": seconds(cake_s),
    "kissat_version": subprocess.run(["$KISSAT", "--version"], capture_output=True, text=True).stdout.strip(),
    "artifact_root": "$SCRATCH",
}
pathlib.Path(final).write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
print(json.dumps(payload, indent=2, sort_keys=True))
PY

cp "$ATTACK" "$DTRIM_LOG" "$CAKE_LOG" "$SCRATCH/SHA256SUMS" "$OUTDIR/"
echo ">>> chunk $CHUNK_ID certified against the survey-identical CNF"
