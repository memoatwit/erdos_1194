#!/bin/bash
#SBATCH --job-name=r3_alt_witness1
#SBATCH --partition=cpu
#SBATCH --account=pi_ergezerm_wit_edu
#SBATCH --time=01:00:00
#SBATCH --cpus-per-task=8
#SBATCH --mem=8G
#SBATCH --output=results/slurm_logs/alt-witness1-%j.out
#SBATCH --error=results/slurm_logs/alt-witness1-%j.err

set -euo pipefail
export PATH=/work/pi_ergezerm_wit_edu/ergezerm_wit_edu-conda/envs/soft/bin:$PATH

cd "$HOME/erdos_r3"
mkdir -p results results/slurm_logs

OUT="results/N212_K43_witness_alt1_hamming20.json"
SPLIT_OUT="results/N212_K43_witness_alt1_hamming20_degree_order.json"

if [ -s "$OUT" ] && [ -s "$SPLIT_OUT" ]; then
  echo "[skip] alt witness already exists:"
  ls -l "$OUT" "$SPLIT_OUT"
  exit 0
fi

python r3_alt_witness.py \
  --N 212 \
  --target 43 \
  --base-witness results/N212_K43_witness.json \
  --hamming-min 20 \
  --window-bounds results/b003002.txt \
  --time-limit 3300 \
  --workers 8 \
  --branch-value min \
  --output "$OUT" \
  --split-vars-output "$SPLIT_OUT"

python r3_verify.py "$OUT" --quiet
echo "Done: $OUT"
echo "Done: $SPLIT_OUT"
