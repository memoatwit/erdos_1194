#!/bin/bash
#SBATCH --job-name=r3_212_p2_11575_111574
#SBATCH --partition=cpu
#SBATCH --account=pi_ergezerm_wit_edu
#SBATCH --time=02:00:00
#SBATCH --array=0-1999%200
#SBATCH --cpus-per-task=8
#SBATCH --mem=8G
#SBATCH --output=results/slurm_logs/phase2-%A_%a.out
#SBATCH --error=results/slurm_logs/phase2-%A_%a.err

set -euo pipefail
export PATH=/work/pi_ergezerm_wit_edu/ergezerm_wit_edu-conda/envs/soft/bin:$PATH

cd $HOME/erdos_r3

CHUNK_START=11575
CHUNK_END=111575
CHUNKS_PER_TASK=50
RANGE_START=$((CHUNK_START + SLURM_ARRAY_TASK_ID * CHUNKS_PER_TASK))
RANGE_END=$((RANGE_START + CHUNKS_PER_TASK))
if [ "$RANGE_END" -gt "$CHUNK_END" ]; then
  RANGE_END="$CHUNK_END"
fi
RANGE_END_INCLUSIVE=$((RANGE_END - 1))

SHARD_DIR="$HOME/erdos_r3/results/broad24_window_alt1_11575_111574"
mkdir -p "$SHARD_DIR"
SHARD_FILE="$SHARD_DIR/chunks_$(printf '%08d' $RANGE_START)_$(printf '%08d' $RANGE_END_INCLUSIVE).jsonl"
TMP_SHARD_FILE="$SHARD_FILE.tmp_${SLURM_JOB_ID}_${SLURM_ARRAY_TASK_ID}"

# Skip if the final shard already exists and is non-empty (allows resume).
if [ -s "$SHARD_FILE" ]; then
  echo "[skip] $SHARD_FILE already exists"
  exit 0
fi
rm -f "$TMP_SHARD_FILE"

python3 "$HOME/erdos_r3/r3_split_cpsat.py" \
  --N 212 --K 44 \
  --pairs 24 \
  --strategy degree-vars \
  --split-count 24 \
  --split-vars "$HOME/erdos_r3/results/N212_K43_witness_alt1_hamming20_degree_order.json" \
  --chunk-id-start "$RANGE_START" \
  --chunk-id-end "$RANGE_END" \
  --chunk-time-limit 60 \
  --workers-per-chunk 8 \
  --hint "$HOME/erdos_r3/results/N212_K43_witness_alt1_hamming20.json" \
  --fix-in "$HOME/erdos_r3/results/N212_K44_force_endpoints.json" \
  --window-bounds "$HOME/erdos_r3/results/b003002.txt" \
  --prune-prefix-ap \
  --branch-order degree \
  --branch-value min \
  --fixed-search \
  --quiet \
  --progress-every 5000 \
  --output "$TMP_SHARD_FILE"

mv "$TMP_SHARD_FILE" "$SHARD_FILE"
