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

set -euo pipefail
export PATH=/work/pi_ergezerm_wit_edu/ergezerm_wit_edu-conda/envs/soft/bin:$PATH

cd $HOME/erdos_r3

PARENT_JSONL="$HOME/erdos_r3/results/refine_N212_K44_window100k_sample500_tail_level3_base65535_sub1535_subchunk3_next8_60.jsonl"
PARENT_CHUNK_ID=0

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
  OUT="$HOME/erdos_r3/results/pair_bench_level3_base65535_sub1535_subchunk3_control_v2.jsonl"
  python r3_split_cpsat.py $COMMON_FLAGS --output "$OUT"
else
  OUT="$HOME/erdos_r3/results/pair_bench_level3_base65535_sub1535_subchunk3_treatment_v2.jsonl"
  python r3_split_cpsat.py $COMMON_FLAGS --pair-clauses-window 67,91 --output "$OUT"
fi

echo "Done: $OUT"
