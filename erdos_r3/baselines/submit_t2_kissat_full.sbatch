#!/bin/bash
#SBATCH --job-name=r3_t2_kissat_full
#SBATCH --partition=cpu
#SBATCH --account=pi_ergezerm_wit_edu
#SBATCH --time=08:30:00
#SBATCH --array=0-1517%200
#SBATCH --cpus-per-task=1
#SBATCH --mem=8G
#SBATCH --output=results/slurm_logs/t2_full-%A_%a.out
#SBATCH --error=results/slurm_logs/t2_full-%A_%a.err
#SBATCH --chdir=/work/pi_ergezerm_wit_edu/ergezerm_wit_edu/erdos_r3

# Full T2 survey: re-attack all 6,071 broad CP-SAT UNKNOWN chunks with
# kissat 4.0.4, using the same no-window CNF encoding as the seed-42 pilot.
# Proofs are intentionally discarded; this run measures coverage and tail
# behavior. Any SAT row is an emergency candidate 44-set and cancels the array.

set -euo pipefail
export PATH=/work/pi_ergezerm_wit_edu/ergezerm_wit_edu-conda/envs/soft/bin:$PATH

R3_DIR=${R3_DIR:-/work/pi_ergezerm_wit_edu/ergezerm_wit_edu/erdos_r3}
cd "$R3_DIR"
mkdir -p results/baselines/t2_full results/baselines/scratch_t2_full results/slurm_logs

KISSAT="$R3_DIR/bin/kissat"
INPUT="results/N212_K44_window100k_unknowns.jsonl"
[ -x "$KISSAT" ] || { echo "missing $KISSAT" >&2; exit 1; }
[ "$(wc -l < "$INPUT")" -eq 6071 ] || { echo "expected 6071 T2 rows" >&2; exit 1; }

VERSION=$($KISSAT --version | head -1)

# Four sequential chunks per array element keep the submitted array below
# Unity's 2,000-job QOS limit. Every chunk still receives its own 2-hour cap.
for OFFSET in 0 1 2 3; do
  IDX=$((SLURM_ARRAY_TASK_ID * 4 + OFFSET))
  [ "$IDX" -lt 6071 ] || continue
  OUT="results/baselines/t2_full/t2_kissat_idx$(printf '%04d' "$IDX").jsonl"
  if [ -s "$OUT" ]; then
    echo "[skip] $OUT already exists"
    continue
  fi
  TMP="$OUT.tmp_${SLURM_JOB_ID}_${SLURM_ARRAY_TASK_ID}"
  set +e
  python r3_sat_attack.py \
    --input "$INPUT" \
    --N 212 --K 44 \
    --window-bounds results/b003002.txt \
    --window-lengths none \
    --array-index "$IDX" \
    --time-limit 7200 \
    --solver-binary "$KISSAT" \
    --solver-label kissat-no-windows \
    --solver-version "$VERSION" \
    --discard-external-proof \
    --work-dir results/baselines/scratch_t2_full \
    --output "$TMP"
  RC=$?
  set -e
  mv "$TMP" "$OUT"
  if [ "$RC" -ne 0 ] || grep -q '"status": "SAT"' "$OUT"; then
    echo "!!! SAT row: verify the candidate immediately with r3_verify.py" >&2
    scancel "$SLURM_ARRAY_JOB_ID"
    exit 1
  fi
done
