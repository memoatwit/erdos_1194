#!/bin/bash
#SBATCH --job-name=r3_t1c_cert
#SBATCH --partition=cpu
#SBATCH --account=pi_ergezerm_wit_edu
#SBATCH --time=72:30:00
#SBATCH --array=0-1
#SBATCH --cpus-per-task=1
#SBATCH --mem=64G
#SBATCH --output=results/slurm_logs/t1c_cert-%A_%a.out
#SBATCH --error=results/slurm_logs/t1c_cert-%A_%a.err
#SBATCH --chdir=/work/pi_ergezerm_wit_edu/ergezerm_wit_edu/erdos_r3
#
# End-to-end certificate provenance for T1c, fixing the NOT_VERIFIED issue:
# the first verification pass ran drat-trim against REGENERATED CNFs, which
# evidently differ from the formulas the original kissat run refuted.
#
# This job removes all ambiguity by doing solve + verify against the SAME
# file in one task:
#   1. kissat 4.0.4 on the archived CNF results/baselines/t1c_proofs/chunk_*.cnf
#      (sha256-pinned in SHA256SUMS), emitting a fresh DRAT proof;
#   2. drat-trim verification of that proof against that exact CNF;
#   3. a provenance JSON recording sha256 of CNF and proof, solver/verifier
#      versions, times, and statuses.
#
# Expected solve ~4-5 h per chunk (deterministic single-threaded kissat on
# the same encoding), verify up to ~24 h; 72 h wall is generous headroom.
# On VERIFIED: flip the %% TODO-VERIFY wording in paper/paper.body.tex from
# "solver-reported" to "certified", and archive CNF+proof+SHA256 to Zenodo.

set -euo pipefail
export PATH=/work/pi_ergezerm_wit_edu/ergezerm_wit_edu-conda/envs/soft/bin:$PATH

R3_DIR=${R3_DIR:-/work/pi_ergezerm_wit_edu/ergezerm_wit_edu/erdos_r3}
cd "$R3_DIR"
mkdir -p results/baselines/t1c_certified results/slurm_logs

KISSAT="$R3_DIR/bin/kissat"
DRATTRIM="$R3_DIR/drat-trim"
[ -x "$KISSAT" ] || { echo "missing $KISSAT (bash baselines/build_kissat.sh)" >&2; exit 1; }
if [ ! -x "$DRATTRIM" ]; then
  DRAT_TRIM_DIR="$R3_DIR/tools/drat-trim" DRAT_TRIM_BIN="$DRATTRIM" \
    bash "$R3_DIR/build_drat_trim.sh" 1>&2
fi

case $SLURM_ARRAY_TASK_ID in
  0) CHUNK_ID=40959 ;;
  1) CHUNK_ID=48895 ;;
  *) echo "unexpected array index" >&2; exit 2 ;;
esac

CNF="$R3_DIR/results/baselines/t1c_proofs/chunk_$(printf '%08d' $CHUNK_ID).cnf"
[ -s "$CNF" ] || { echo "missing archived CNF: $CNF" >&2; exit 1; }

OUTDIR="$R3_DIR/results/baselines/t1c_certified"
PROOF="$OUTDIR/chunk_$(printf '%08d' $CHUNK_ID).cert.drat"
META="$OUTDIR/chunk_${CHUNK_ID}_provenance.json"
if [ -s "$META" ]; then
  echo "[skip] $META already exists"
  exit 0
fi

echo "[solve] kissat on $CNF"
T0=$(date +%s)
set +e
"$KISSAT" --time=64800 "$CNF" "$PROOF" > "$OUTDIR/chunk_${CHUNK_ID}.kissat.log" 2>&1
KEXIT=$?
set -e
T1=$(date +%s)
SOLVE_S=$((T1 - T0))
# kissat exit codes: 10 = SAT, 20 = UNSAT
STATUS=UNKNOWN
[ $KEXIT -eq 20 ] && STATUS=UNSAT
[ $KEXIT -eq 10 ] && STATUS=SAT
echo "[solve] status=$STATUS exit=$KEXIT seconds=$SOLVE_S"

VERIFY=SKIPPED
VERIFY_S=0
if [ "$STATUS" = "UNSAT" ] && [ -s "$PROOF" ]; then
  echo "[verify] drat-trim on the same CNF + fresh proof"
  T2=$(date +%s)
  set +e
  "$DRATTRIM" "$CNF" "$PROOF" -t 165000 > "$OUTDIR/chunk_${CHUNK_ID}.dtrim.log" 2>&1
  DEXIT=$?
  set -e
  T3=$(date +%s)
  VERIFY_S=$((T3 - T2))
  if grep -q "s VERIFIED" "$OUTDIR/chunk_${CHUNK_ID}.dtrim.log"; then
    VERIFY=VERIFIED
  else
    VERIFY=NOT_VERIFIED
  fi
  echo "[verify] $VERIFY exit=$DEXIT seconds=$VERIFY_S"
fi

python - "$META" <<PY
import hashlib, json, subprocess, sys
def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as fh:
        for b in iter(lambda: fh.read(1 << 22), b""):
            h.update(b)
    return h.hexdigest()
meta = {
    "chunk_id": $CHUNK_ID,
    "status": "$STATUS",
    "verify": "$VERIFY",
    "solve_seconds": $SOLVE_S,
    "verify_seconds": $VERIFY_S,
    "cnf": "$CNF",
    "cnf_sha256": sha("$CNF"),
    "proof": "$PROOF",
    "proof_sha256": sha("$PROOF") if "$STATUS" == "UNSAT" else None,
    "kissat_version": subprocess.run(["$KISSAT", "--version"],
        capture_output=True, text=True).stdout.strip(),
}
open(sys.argv[1], "w").write(json.dumps(meta, indent=2) + "\n")
print(json.dumps(meta, indent=2))
PY

echo "Done: $META"
[ "$VERIFY" = "VERIFIED" ] && echo ">>> chunk $CHUNK_ID: certified end-to-end. Flip TODO-VERIFY in the paper when both chunks report this."
[ "$STATUS" = "SAT" ] && echo "!!! SAT — verify witness with r3_verify.py IMMEDIATELY"
exit 0
