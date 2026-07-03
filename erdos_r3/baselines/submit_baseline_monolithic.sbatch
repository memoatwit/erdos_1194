#!/bin/bash
#SBATCH --job-name=r3_mono_base
#SBATCH --partition=cpu
#SBATCH --account=pi_ergezerm_wit_edu
#SBATCH --time=24:30:00
#SBATCH --array=0-5
#SBATCH --cpus-per-task=8
#SBATCH --mem=32G
#SBATCH --output=results/slurm_logs/mono_base-%A_%a.out
#SBATCH --error=results/slurm_logs/mono_base-%A_%a.err
#SBATCH --chdir=/work/pi_ergezerm_wit_edu/ergezerm_wit_edu/erdos_r3
#
# Monolithic-baseline experiment for the Constraints revision:
# what does each solver paradigm do on the FULL unsplit r_3(212) <= 43
# decision instance, with no witness-split pins?
#
# Array cells (paradigm x window-bounds):
#   0: CP-SAT,  windows ON      1: CP-SAT,  windows OFF
#   2: HiGHS,   windows ON      3: HiGHS,   windows OFF
#   4: CDCL,    windows ON      5: CDCL,    windows OFF
#
# Per-task wall: 24 h solver cap + 30 min headroom.
# Total compute: 6 tasks * 8 cores * 24 h = 1,152 CPU-hours (CDCL uses 1
# core; the 8-core allocation keeps cells uniform and gives encode headroom).
#
# Results land in results/baselines/ as JSON; the table for the paper
# (Section 3, "monolithic baseline") reads straight off the six status rows.

set -euo pipefail
export PATH=/work/pi_ergezerm_wit_edu/ergezerm_wit_edu-conda/envs/soft/bin:$PATH

R3_DIR=${R3_DIR:-/work/pi_ergezerm_wit_edu/ergezerm_wit_edu/erdos_r3}
cd "$R3_DIR"
mkdir -p results/baselines results/slurm_logs results/baselines/scratch

TIME_LIMIT=86400
BFILE="results/b003002.txt"

case $SLURM_ARRAY_TASK_ID in
  0) PARADIGM=cpsat; WIN=on  ;;
  1) PARADIGM=cpsat; WIN=off ;;
  2) PARADIGM=highs; WIN=on  ;;
  3) PARADIGM=highs; WIN=off ;;
  4) PARADIGM=cdcl;  WIN=on  ;;
  5) PARADIGM=cdcl;  WIN=off ;;
esac

TAG="${PARADIGM}_monolithic_${WIN}win"
OUT="results/baselines/${TAG}.json"
if [ -s "$OUT" ]; then
  echo "[skip] $OUT already exists"
  exit 0
fi

echo "[run] paradigm=$PARADIGM windows=$WIN wall=${TIME_LIMIT}s"

case $PARADIGM in
  cpsat)
    WINARG=""
    if [ "$WIN" = "on" ]; then WINARG="--window-bounds $BFILE"; fi
    python r3_cpsat.py 212 \
      --decision-size 44 \
      --time-limit $TIME_LIMIT \
      --workers 8 \
      $WINARG \
      --output "$OUT"
    ;;
  highs)
    WINARG=""
    if [ "$WIN" = "on" ]; then WINARG="--windows"; fi
    python baselines/r3_monolithic_highs.py \
      $WINARG \
      --time-limit $TIME_LIMIT \
      --threads 8 \
      --output "$OUT"
    ;;
  cdcl)
    # Monolithic chunk = a single row with no pins.
    MONO="results/baselines/monolithic_chunk.jsonl"
    if [ ! -s "$MONO" ]; then
      python - "$MONO" <<'PY'
import json, sys
row = {"chunk_id": 0, "N": 212, "K": 44, "fixed_in": [], "fixed_out": []}
open(sys.argv[1], "w").write(json.dumps(row) + "\n")
PY
    fi
    if [ "$WIN" = "on" ]; then WINLEN=""; else WINLEN="--window-lengths none"; fi
    python r3_sat_attack.py \
      --input "$MONO" \
      --N 212 --K 44 \
      --window-bounds "$BFILE" \
      $WINLEN \
      --array-index 0 \
      --time-limit $TIME_LIMIT \
      --solver-binary pysat:auto \
      --work-dir results/baselines/scratch \
      --output "$OUT"
    ;;
esac

echo "Done: $OUT"

# A SAT/FEASIBLE result here would disprove r_3(212) <= 43 — flag loudly.
if grep -qE '"status": *"(SAT|FEASIBLE)"' "$OUT"; then
  echo "!!! FEASIBLE/SAT on the monolithic instance — verify the witness immediately:"
  echo "    python r3_verify.py --check-witness $OUT"
fi
