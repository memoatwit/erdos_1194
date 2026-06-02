#!/bin/bash
#SBATCH --job-name=r3_pair_clauses_bench
#SBATCH --partition=cpu
#SBATCH --account=pi_ergezerm_wit_edu
#SBATCH --time=01:00:00
#SBATCH --array=0-1
#SBATCH --cpus-per-task=8
#SBATCH --mem=8G
#SBATCH --output=results/slurm_logs/pair_bench-%A_%a.out
#SBATCH --error=results/slurm_logs/pair_bench-%A_%a.err
#
# A/B benchmark: re-solve a single hard residual subchunk with and without the
# targeted pair-AND propagation clauses on midpoints [67, 91].  Same wall cap
# (600s) and same fixed-search settings for both runs.
#
# BEFORE SUBMITTING:
#  1) Pick one of the 6 level-3 UNKNOWN residuals.  List them on Unity with:
#       grep -lH '"status": *"UNKNOWN"' \
#         results/refine_N212_K44_window100k_sample500_tail_level3_*_next8_60.jsonl
#  2) Fill in PARENT_JSONL (full Unity path to that level-3 file) and
#     PARENT_CHUNK_ID (the chunk_id of the UNKNOWN row inside it).
#  3) Submit:  sbatch bench_pair_clauses_template.sbatch

set -euo pipefail
export PATH=/work/pi_ergezerm_wit_edu/ergezerm_wit_edu-conda/envs/soft/bin:$PATH

cd $HOME/erdos_r3

# === FILL THESE TWO LINES ===
PARENT_JSONL="$HOME/erdos_r3/results/refine_N212_K44_window100k_sample500_tail_level3_baseXXXXX_subYYYY_subchunkZ_next8_60.jsonl"
PARENT_CHUNK_ID=0
# ============================

# Both arms split 8 more vars off the parent, with a 600s wall cap.
COMMON_FLAGS="--N 212 --K 44 \
  --pairs 8 \
  --strategy degree-vars \
  --split-count 8 \
  --split-vars $HOME/erdos_r3/results/N212_K43_witness_degree_order.json \
  --base-jsonl $PARENT_JSONL \
  --base-chunk-id $PARENT_CHUNK_ID \
  --chunk-time-limit 600 \
  --workers-per-chunk 8 \
  --hint $HOME/erdos_r3/results/N212_K43_witness.json \
  --fix-in $HOME/erdos_r3/results/N212_K44_force_endpoints.json \
  --window-bounds $HOME/erdos_r3/results/b003002.txt \
  --prune-prefix-ap \
  --branch-order degree \
  --branch-value min \
  --fixed-search \
  --quiet \
  --progress-every 1000"

if [ "$SLURM_ARRAY_TASK_ID" -eq 0 ]; then
  OUT="$HOME/erdos_r3/results/pair_bench_control.jsonl"
  python r3_split_cpsat.py $COMMON_FLAGS --output "$OUT"
else
  OUT="$HOME/erdos_r3/results/pair_bench_treatment.jsonl"
  python r3_split_cpsat.py $COMMON_FLAGS --pair-clauses-window 67,91 --output "$OUT"
fi

echo "Done: $OUT"
