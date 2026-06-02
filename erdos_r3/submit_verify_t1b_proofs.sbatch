#!/bin/bash
#SBATCH --job-name=r3_drat_verify
#SBATCH --partition=cpu
#SBATCH --account=pi_ergezerm_wit_edu
#SBATCH --time=01:15:00
#SBATCH --array=0-16%17
#SBATCH --cpus-per-task=1
#SBATCH --mem=8G
#SBATCH --output=results/slurm_logs/drat_verify-%A_%a.out
#SBATCH --error=results/slurm_logs/drat_verify-%A_%a.err
#
# drat-trim verification pass on the 17 T1b UNSAT closures with emitted DRAT
# files from the
# proof-producing rerun (Unity job 58913424). One SLURM task per chunk,
# single-threaded. Verification typically runs 2-5x faster than the original
# CDCL emission, so a 1h wall is comfortable headroom.
#
# Per-task wall: 1h drat-trim cap + 15 min headroom = 1.25h SBATCH time.
# Total compute: 17 tasks * 1 core * <=1h = up to 17 CPU-hours.
#
# Note: the array indexes T1B_UNSAT_CHUNK_IDS_ORDERED in verify_t1b_proofs.py,
# which is the 20-chunk T1b list minus the 2 T1c residuals (40959, 48895) and
# proof-timeout chunk 32735. Indices 0..16 therefore map cleanly to the 17
# chunks that produced DRAT proofs in the proof-producing rerun.

set -euo pipefail
export PATH=/work/pi_ergezerm_wit_edu/ergezerm_wit_edu-conda/envs/soft/bin:$PATH

cd $HOME/erdos_r3

# Build drat-trim if not already present.
if [ ! -x "$HOME/erdos_r3/drat-trim" ]; then
  bash "$HOME/erdos_r3/build_drat_trim.sh" 1>&2
fi

PROOFS_DIR="$HOME/erdos_r3/results/sat_t1b_proofs/scratch"
CNFS_DIR="$HOME/erdos_r3/results/sat_t1b_proofs/scratch"
OUT_DIR="$PROOFS_DIR/verification_shards"
LRAT_DIR="$PROOFS_DIR/lrat"
mkdir -p "$OUT_DIR" "$LRAT_DIR"

OUT="$OUT_DIR/verify_idx$(printf '%02d' $SLURM_ARRAY_TASK_ID).jsonl"
if [ -s "$OUT" ]; then
  echo "[skip] $OUT already exists"
  exit 0
fi
TMP="$OUT.tmp_${SLURM_JOB_ID}_${SLURM_ARRAY_TASK_ID}"
rm -f "$TMP"

python "$HOME/erdos_r3/verify_t1b_proofs.py" \
  --proofs-dir "$PROOFS_DIR" \
  --cnfs-dir "$CNFS_DIR" \
  --output "$TMP" \
  --drat-trim "$HOME/erdos_r3/drat-trim" \
  --array-index $SLURM_ARRAY_TASK_ID \
  --time-limit 3600 \
  --emit-lrat \
  --lrat-dir "$LRAT_DIR"

mv "$TMP" "$OUT"
echo "Done: $OUT"
