#!/bin/bash
#SBATCH --job-name=r3_known_reg
#SBATCH --partition=cpu
#SBATCH --account=pi_ergezerm_wit_edu
#SBATCH --time=24:30:00
#SBATCH --array=0-2%3
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --output=results/slurm_logs/known_reg-%A_%a.out
#SBATCH --error=results/slurm_logs/known_reg-%A_%a.err
#SBATCH --chdir=/work/pi_ergezerm_wit_edu/ergezerm_wit_edu/erdos_r3

# End-to-end regressions at exact OEIS values:
#   r_3(100)=27, r_3(150)=35, r_3(200)=41.
# Each task finds and verifies a witness of the known size, then asks kissat
# for size+1 and verifies the resulting DRAT proof. Window bounds are truncated
# to lengths strictly below N, avoiding the circular full-length inequality.

set -euo pipefail
export PATH=/work/pi_ergezerm_wit_edu/ergezerm_wit_edu-conda/envs/soft/bin:$PATH

R3_DIR=${R3_DIR:-/work/pi_ergezerm_wit_edu/ergezerm_wit_edu/erdos_r3}
cd "$R3_DIR"
mkdir -p results/baselines/known_regression results/slurm_logs

case $SLURM_ARRAY_TASK_ID in
  0) N=100; KNOWN=27 ;;
  1) N=150; KNOWN=35 ;;
  2) N=200; KNOWN=41 ;;
  *) exit 2 ;;
esac
TARGET=$((KNOWN + 1))
OUTDIR="$R3_DIR/results/baselines/known_regression/N${N}"
mkdir -p "$OUTDIR"
META="$OUTDIR/provenance.json"
if [ -s "$META" ]; then
  echo "[skip] $META already exists"
  exit 0
fi

KISSAT="$R3_DIR/bin/kissat"
DRATTRIM="$R3_DIR/drat-trim"
[ -x "$KISSAT" ] || { echo "missing $KISSAT" >&2; exit 1; }
if [ ! -x "$DRATTRIM" ]; then
  DRAT_TRIM_DIR="$R3_DIR/tools/drat-trim" DRAT_TRIM_BIN="$DRATTRIM" \
    bash "$R3_DIR/build_drat_trim.sh"
fi

BFILE="$OUTDIR/b003002_lt_${N}.txt"
awk -v n="$N" '$1 < n {print}' results/b003002.txt > "$BFILE"
INSTANCE="$OUTDIR/instance.jsonl"
printf '{"chunk_id": %d, "N": %d, "K": %d, "fixed_in": [], "fixed_out": []}\n' \
  "$N" "$N" "$TARGET" > "$INSTANCE"

echo "[lower] finding size-$KNOWN witness for N=$N"
set +e
python r3_cpsat.py "$N" \
  --decision-size "$KNOWN" \
  --time-limit 3600 \
  --workers 8 \
  --branch-order degree \
  --branch-value max \
  --window-bounds "$BFILE" \
  --witness \
  --output "$OUTDIR/lower_witness.json"
LOWER_RC=$?
set -e

echo "[upper] refuting size-$TARGET for N=$N"
VERSION=$($KISSAT --version | head -1)
set +e
python r3_sat_attack.py \
  --input "$INSTANCE" \
  --N "$N" --K "$TARGET" \
  --window-bounds "$BFILE" \
  --array-index 0 \
  --time-limit 43200 \
  --solver-binary "$KISSAT" \
  --solver-label kissat-regression \
  --solver-version "$VERSION" \
  --keep-cnf \
  --work-dir "$OUTDIR" \
  --output "$OUTDIR/upper_attack.jsonl"
UPPER_RC=$?
set -e

CNF="$OUTDIR/chunk_$(printf '%08d' "$N").cnf"
PROOF="$OUTDIR/chunk_$(printf '%08d' "$N").drat"
VERIFY=SKIPPED
VERIFY_SECONDS=0
UPPER_STATUS=$(python - "$OUTDIR/upper_attack.jsonl" <<'PY'
import json, sys
rows=[json.loads(x) for x in open(sys.argv[1]) if x.strip()]
print(rows[-1]["status"] if rows else "MISSING")
PY
)
if [ "$UPPER_STATUS" = "UNSAT" ] && [ -s "$CNF" ] && [ -s "$PROOF" ]; then
  START=$(date +%s)
  set +e
  "$DRATTRIM" "$CNF" "$PROOF" -t 43200 > "$OUTDIR/drat-trim.log" 2>&1
  DTRC=$?
  set -e
  VERIFY_SECONDS=$(($(date +%s) - START))
  if grep -q 's VERIFIED' "$OUTDIR/drat-trim.log"; then
    VERIFY=VERIFIED
  else
    VERIFY=NOT_VERIFIED
  fi
fi

python - "$META" "$OUTDIR/lower_witness.json" "$OUTDIR/upper_attack.jsonl" \
  "$CNF" "$PROOF" <<PY
import hashlib, json, pathlib, sys
def sha(path):
    p=pathlib.Path(path)
    if not p.is_file(): return None
    h=hashlib.sha256()
    with p.open("rb") as fh:
        for block in iter(lambda: fh.read(1 << 22), b""):
            h.update(block)
    return h.hexdigest()
lower=json.load(open(sys.argv[2])) if pathlib.Path(sys.argv[2]).is_file() else {}
upper_rows=[json.loads(x) for x in open(sys.argv[3]) if x.strip()]
upper=upper_rows[-1] if upper_rows else {}
payload={
    "N": $N,
    "known_r3": $KNOWN,
    "target_refuted": $TARGET,
    "lower_exit_code": $LOWER_RC,
    "lower_status": lower.get("solver_status_name"),
    "lower_witness_verified": lower.get("witness_verified", False),
    "upper_exit_code": $UPPER_RC,
    "upper_status": upper.get("status"),
    "upper_cnf_sha256": sha(sys.argv[4]),
    "upper_proof_sha256": sha(sys.argv[5]),
    "proof_verification": "$VERIFY",
    "proof_verify_seconds": $VERIFY_SECONDS,
    "window_bounds_max_length": $((N - 1)),
}
open(sys.argv[1], "w").write(json.dumps(payload, indent=2)+"\n")
print(json.dumps(payload, indent=2))
PY

if [ "$UPPER_STATUS" = "SAT" ]; then
  echo "!!! regression returned SAT above the recorded exact value" >&2
  scancel "$SLURM_ARRAY_JOB_ID"
  exit 1
fi
if [ "$VERIFY" != "VERIFIED" ]; then
  echo "regression incomplete: upper=$UPPER_STATUS verify=$VERIFY" >&2
fi
