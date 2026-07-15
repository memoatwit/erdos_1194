#!/bin/bash
#SBATCH --job-name=r3_exact_cert
#SBATCH --partition=cpu
#SBATCH --account=pi_ergezerm_wit_edu
#SBATCH --time=72:30:00
#SBATCH --array=0-2%3
#SBATCH --cpus-per-task=1
#SBATCH --mem=64G
#SBATCH --output=results/slurm_logs/exact_cert-%A_%a.out
#SBATCH --error=results/slurm_logs/exact_cert-%A_%a.err
#SBATCH --chdir=/work/pi_ergezerm_wit_edu/ergezerm_wit_edu/erdos_r3

# End-to-end exact-value certificates for the three largest successful
# calibration cases. Every task independently:
#   1. finds and verifies a lower witness of size r_3(N);
#   2. regenerates the calibrated pure 3-AP/cardinality CNF for r_3(N)+1;
#   3. runs proof-producing Kissat 4.0.4;
#   4. checks the DRAT proof and converts it to LRAT with drat-trim -L;
#   5. checks the LRAT proof with the formally verified cake_lpr checker;
#   6. writes compact provenance under /work while retaining large artifacts
#      in the user's project scratch directories.

set -euo pipefail
export PATH=/work/pi_ergezerm_wit_edu/ergezerm_wit_edu-conda/envs/soft/bin:$PATH

R3_DIR=${R3_DIR:-/work/pi_ergezerm_wit_edu/ergezerm_wit_edu/erdos_r3}
cd "$R3_DIR"
mkdir -p results/baselines/known_exact_certified results/slurm_logs

case ${SLURM_ARRAY_TASK_ID:?missing SLURM_ARRAY_TASK_ID} in
  0)
    N=100; KNOWN=27
    SCRATCH_ROOT=/scratch4/workspace/ergezerm_wit_edu-soft_speech
    ;;
  1)
    N=90; KNOWN=24
    SCRATCH_ROOT=/scratch3/workspace/ergezerm_wit_edu-superfund
    ;;
  2)
    N=80; KNOWN=22
    SCRATCH_ROOT=/scratch4/workspace/ergezerm_wit_edu-soft_speech
    ;;
  *) exit 2 ;;
esac
TARGET=$((KNOWN + 1))

OUTDIR="$R3_DIR/results/baselines/known_exact_certified/N${N}"
SCRATCH="$SCRATCH_ROOT/r3_exact_certified/N${N}"
mkdir -p "$OUTDIR" "$SCRATCH"

FINAL="$OUTDIR/provenance.json"
if [ -s "$FINAL" ] && grep -q '"cake_lpr_status": "VERIFIED"' "$FINAL"; then
  echo "[skip] already certified: $FINAL"
  exit 0
fi

KISSAT="$R3_DIR/bin/kissat"
DRATTRIM="$R3_DIR/drat-trim"
CAKELPR="$R3_DIR/bin/cake_lpr"
[ -x "$KISSAT" ] || { echo "missing $KISSAT" >&2; exit 1; }
[ -x "$DRATTRIM" ] || { echo "missing $DRATTRIM" >&2; exit 1; }
[ -x "$CAKELPR" ] || { echo "missing $CAKELPR" >&2; exit 1; }

echo "[setup] N=$N known=$KNOWN target=$TARGET scratch=$SCRATCH"
echo "[setup] kissat=$($KISSAT --version | head -1)"

# Lower-bound witness, deliberately without window inequalities.
LOWER_SOLVER="$SCRATCH/lower_solver.json"
LOWER_CANDIDATE="$SCRATCH/lower_candidate.json"
LOWER_VERIFY="$SCRATCH/lower_verify.json"
LOWER_SOURCE_FILE="$SCRATCH/lower_source.txt"
KNOWN_REGRESSION_LOWER="$R3_DIR/results/baselines/known_regression/N${N}/lower_witness.json"

# Prefer a previously audited witness when available. In particular, the
# earlier N=100 regression found and independently verified a size-27 witness
# with eight CP-SAT workers, while a fresh single-worker search can time out.
if [ -s "$KNOWN_REGRESSION_LOWER" ] && python - "$KNOWN_REGRESSION_LOWER" "$KNOWN" <<'PY'
import json, sys
row = json.load(open(sys.argv[1]))
ok = (
    row.get("solver_status_name") in {"OPTIMAL", "FEASIBLE"}
    and row.get("witness_verified") is True
    and len(row.get("witness", [])) == int(sys.argv[2])
)
raise SystemExit(0 if ok else 1)
PY
then
  cp "$KNOWN_REGRESSION_LOWER" "$LOWER_SOLVER"
  printf '%s\n' "$KNOWN_REGRESSION_LOWER" > "$LOWER_SOURCE_FILE"
fi

if [ ! -s "$LOWER_SOLVER" ]; then
  python r3_cpsat.py "$N" \
    --decision-size "$KNOWN" \
    --time-limit 7200 \
    --workers 1 \
    --branch-order degree \
    --branch-value max \
    --witness \
    --output "$LOWER_SOLVER" \
    > "$SCRATCH/lower_solver.log" 2>&1
  printf '%s\n' fresh-pure-cpsat > "$LOWER_SOURCE_FILE"
fi

python - "$LOWER_SOLVER" "$LOWER_CANDIDATE" "$N" "$KNOWN" <<'PY'
import json, pathlib, sys
source, target, n, known = sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4])
row = json.load(open(source))
witness = row.get("witness", [])
if row.get("solver_status_name") not in {"OPTIMAL", "FEASIBLE"}:
    raise SystemExit(f"lower solver did not find a witness: {row.get('solver_status_name')}")
if len(witness) != known:
    raise SystemExit(f"lower witness has size {len(witness)}, expected {known}")
pathlib.Path(target).write_text(json.dumps({"N": n, "A": witness}, indent=2) + "\n")
PY
python - "$LOWER_CANDIDATE" "$LOWER_VERIFY" <<'PY'
import json, pathlib, sys
from r3_verify import verify

candidate = json.load(open(sys.argv[1]))
report = verify(candidate["A"], N=candidate["N"])
pathlib.Path(sys.argv[2]).write_text(json.dumps(report, indent=2) + "\n")
if not report.get("ok"):
    raise SystemExit("lower witness failed independent verification")
PY

# Regenerate and solve exactly the same pure formula used in calibration.
INSTANCE="$SCRATCH/instance.jsonl"
printf '{"chunk_id": %d, "N": %d, "K": %d, "fixed_in": [], "fixed_out": []}\n' \
  "$N" "$N" "$TARGET" > "$INSTANCE"
UPPER="$SCRATCH/upper_attack.jsonl"
if [ ! -s "$UPPER" ]; then
  python r3_sat_attack.py \
    --input "$INSTANCE" \
    --N "$N" --K "$TARGET" \
    --window-bounds results/b003002.txt \
    --window-lengths none \
    --array-index 0 \
    --time-limit 43200 \
    --solver-binary "$KISSAT" \
    --solver-label kissat-exact-certified-pure \
    --solver-version "$($KISSAT --version | head -1)" \
    --keep-cnf \
    --work-dir "$SCRATCH" \
    --output "$UPPER" \
    > "$SCRATCH/upper_driver.log" 2>&1
fi

UPPER_STATUS=$(python - "$UPPER" <<'PY'
import json, sys
rows = [json.loads(line) for line in open(sys.argv[1]) if line.strip()]
print(rows[-1].get("status", "MISSING") if rows else "MISSING")
PY
)
if [ "$UPPER_STATUS" = SAT ]; then
  echo "!!! SAT above recorded exact value: verify immediately" >&2
  scancel "$SLURM_ARRAY_JOB_ID"
  exit 3
fi
if [ "$UPPER_STATUS" != UNSAT ]; then
  echo "upper proof did not close: $UPPER_STATUS" >&2
  exit 4
fi

PADDED=$(printf '%08d' "$N")
CNF="$SCRATCH/chunk_${PADDED}.cnf"
DRAT="$SCRATCH/chunk_${PADDED}.drat"
LRAT="$SCRATCH/chunk_${PADDED}.lrat"
[ -s "$CNF" ] || { echo "missing CNF: $CNF" >&2; exit 5; }
[ -s "$DRAT" ] || { echo "missing DRAT: $DRAT" >&2; exit 5; }

EXPECTED_HASH=$(python - "$R3_DIR/results/baselines/known_calibration/N${N}/pure/upper_attack.jsonl" <<'PY'
import json, sys
rows = [json.loads(line) for line in open(sys.argv[1]) if line.strip()]
print(rows[-1].get("cnf_sha256", "") if rows else "")
PY
)
ACTUAL_HASH=$(sha256sum "$CNF" | awk '{print $1}')
if [ -z "$EXPECTED_HASH" ] || [ "$EXPECTED_HASH" != "$ACTUAL_HASH" ]; then
  echo "CNF hash mismatch: expected=$EXPECTED_HASH actual=$ACTUAL_HASH" >&2
  exit 6
fi
echo "[encode] calibration CNF hash matched: $ACTUAL_HASH"

# drat-trim is the untrusted converter; cake_lpr independently validates the
# resulting LRAT proof against the archived CNF.
DTRIM_LOG="$SCRATCH/drat-trim.log"
DTRIM_SECONDS_FILE="$SCRATCH/drat-trim.seconds"
if [ ! -s "$LRAT" ] || ! grep -q 's VERIFIED' "$DTRIM_LOG" 2>/dev/null; then
  START=$(date +%s)
  set +e
  "$DRATTRIM" "$CNF" "$DRAT" -t 120000 -L "$LRAT" > "$DTRIM_LOG" 2>&1
  DTRIM_RC=$?
  set -e
  echo $(($(date +%s) - START)) > "$DTRIM_SECONDS_FILE"
  [ "$DTRIM_RC" -eq 0 ] || true
fi
grep -q 's VERIFIED' "$DTRIM_LOG" || { echo "drat-trim did not verify" >&2; exit 7; }
[ -s "$LRAT" ] || { echo "drat-trim emitted no LRAT" >&2; exit 7; }

CAKE_LOG="$SCRATCH/cake_lpr.log"
CAKE_SECONDS_FILE="$SCRATCH/cake_lpr.seconds"
export CML_HEAP_SIZE=${CML_HEAP_SIZE:-24000}
export CML_STACK_SIZE=${CML_STACK_SIZE:-24000}
if ! grep -q 's VERIFIED UNSAT' "$CAKE_LOG" 2>/dev/null; then
  START=$(date +%s)
  set +e
  timeout --signal=TERM 86400 "$CAKELPR" "$CNF" "$LRAT" > "$CAKE_LOG" 2>&1
  CAKE_RC=$?
  set -e
  echo $(($(date +%s) - START)) > "$CAKE_SECONDS_FILE"
  [ "$CAKE_RC" -eq 0 ] || true
fi
grep -q 's VERIFIED UNSAT' "$CAKE_LOG" || { echo "cake_lpr did not verify" >&2; exit 8; }

sha256sum "$CNF" "$DRAT" "$LRAT" > "$SCRATCH/SHA256SUMS"

python - "$FINAL" "$LOWER_SOLVER" "$LOWER_CANDIDATE" "$LOWER_VERIFY" \
  "$UPPER" "$CNF" "$DRAT" "$LRAT" "$SCRATCH" "$EXPECTED_HASH" <<PY
import hashlib, json, pathlib, subprocess, sys

def sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for block in iter(lambda: fh.read(1 << 22), b""):
            h.update(block)
    return h.hexdigest()

def load_json(path):
    return json.load(open(path))

def load_last_jsonl(path):
    rows = [json.loads(line) for line in open(path) if line.strip()]
    return rows[-1] if rows else {}

def integer_file(path):
    p = pathlib.Path(path)
    return int(p.read_text().strip()) if p.is_file() else None

final, lower_solver_path, lower_candidate_path, lower_verify_path, upper_path, cnf, drat, lrat, scratch, expected = sys.argv[1:]
lower_solver = load_json(lower_solver_path)
lower_candidate = load_json(lower_candidate_path)
lower_verify = load_json(lower_verify_path)
upper = load_last_jsonl(upper_path)
payload = {
    "N": $N,
    "known_r3": $KNOWN,
    "target_refuted": $TARGET,
    "lower_solver_status": lower_solver.get("solver_status_name"),
    "lower_witness_source": pathlib.Path(scratch, "lower_source.txt").read_text().strip(),
    "lower_witness": lower_candidate.get("A"),
    "lower_witness_verified": bool(lower_verify.get("ok") and lower_verify.get("size") == $KNOWN),
    "upper_status": upper.get("status"),
    "upper_solver_seconds": upper.get("solver_seconds"),
    "n_vars": upper.get("n_vars"),
    "n_clauses": upper.get("n_clauses"),
    "calibration_cnf_sha256": expected,
    "cnf_sha256": sha(cnf),
    "calibration_hash_match": sha(cnf) == expected,
    "drat_sha256": sha(drat),
    "lrat_sha256": sha(lrat),
    "cnf_bytes": pathlib.Path(cnf).stat().st_size,
    "drat_bytes": pathlib.Path(drat).stat().st_size,
    "lrat_bytes": pathlib.Path(lrat).stat().st_size,
    "drat_trim_status": "VERIFIED",
    "drat_trim_seconds": integer_file(pathlib.Path(scratch) / "drat-trim.seconds"),
    "cake_lpr_status": "VERIFIED",
    "cake_lpr_seconds": integer_file(pathlib.Path(scratch) / "cake_lpr.seconds"),
    "kissat_version": subprocess.run(["$KISSAT", "--version"], capture_output=True, text=True).stdout.strip(),
    "cake_lpr_sha256": sha("$CAKELPR"),
    "drat_trim_sha256": sha("$DRATTRIM"),
    "encoder_sha256": sha("$R3_DIR/r3_sat_attack.py"),
    "artifact_root": scratch,
}
pathlib.Path(final).write_text(json.dumps(payload, indent=2) + "\n")
print(json.dumps(payload, indent=2))
PY

cp "$LOWER_CANDIDATE" "$LOWER_VERIFY" "$UPPER" "$DTRIM_LOG" "$CAKE_LOG" \
  "$SCRATCH/SHA256SUMS" "$OUTDIR/"

echo ">>> N=$N certified exactly: lower witness verified; upper DRAT/LRAT verified by cake_lpr"
