#!/bin/bash
#SBATCH --job-name=r3_t1c_kissat
#SBATCH --partition=cpu
#SBATCH --account=pi_ergezerm_wit_edu
#SBATCH --time=48:30:00
#SBATCH --array=0-3
#SBATCH --cpus-per-task=1
#SBATCH --mem=16G
#SBATCH --output=results/slurm_logs/t1c_kissat-%A_%a.out
#SBATCH --error=results/slurm_logs/t1c_kissat-%A_%a.err
#SBATCH --chdir=/work/pi_ergezerm_wit_edu/ergezerm_wit_edu/erdos_r3
#
# T1c under a competition-grade CDCL solver (kissat) at 48 h — hardens the
# paper's "paradigm-resistant" claim against the obvious referee question
# ("did you try a current competition winner, not just PySAT/CaDiCaL?").
#
# Prereq (once, on a login node):  bash baselines/build_kissat.sh
#
# Array cells (chunk x window-encoding):
#   0: chunk 40959, no windows     1: chunk 48895, no windows
#   2: chunk 40959, windows on     3: chunk 48895, windows on
#
# Total compute: 4 tasks * 1 core * 48 h = 192 CPU-hours.
# DRAT logging is ON: an UNSAT here is a *certifiable close of T1c* — a new
# result. Verify immediately with drat-trim and archive the proof.

set -euo pipefail
export PATH=/work/pi_ergezerm_wit_edu/ergezerm_wit_edu-conda/envs/soft/bin:$PATH

R3_DIR=${R3_DIR:-/work/pi_ergezerm_wit_edu/ergezerm_wit_edu/erdos_r3}
cd "$R3_DIR"
mkdir -p results/baselines results/slurm_logs results/baselines/scratch_t1c

KISSAT="$R3_DIR/bin/kissat"
if [ ! -x "$KISSAT" ]; then
  echo "kissat binary missing — run: bash baselines/build_kissat.sh" >&2
  exit 1
fi

TIME_LIMIT=172800
INPUT="results/N212_K44_t1c2.jsonl"

case $SLURM_ARRAY_TASK_ID in
  0) IDX=0; WIN=off ;;
  1) IDX=1; WIN=off ;;
  2) IDX=0; WIN=on  ;;
  3) IDX=1; WIN=on  ;;
esac

if [ "$WIN" = "on" ]; then WINLEN=""; else WINLEN="--window-lengths none"; fi

OUT="results/baselines/t1c_kissat48h_idx${IDX}_${WIN}win.jsonl"
if [ -s "$OUT" ]; then
  echo "[skip] $OUT already exists"
  exit 0
fi
TMP="$OUT.tmp_${SLURM_JOB_ID}_${SLURM_ARRAY_TASK_ID}"
rm -f "$TMP"

python r3_sat_attack.py \
  --input "$INPUT" \
  --N 212 --K 44 \
  --window-bounds results/b003002.txt \
  $WINLEN \
  --array-index $IDX \
  --time-limit $TIME_LIMIT \
  --solver-binary "$KISSAT" \
  --work-dir results/baselines/scratch_t1c \
  --output "$TMP"

mv "$TMP" "$OUT"
echo "Done: $OUT"

if grep -q '"status": "UNSAT"' "$OUT"; then
  echo "!!! T1c chunk CLOSED by kissat — verify the DRAT proof with drat-trim"
  echo "    and archive it: this changes the paper's headline claim."
fi
if grep -q '"status": "SAT"' "$OUT"; then
  echo "!!! SAT — a 44-set witness under these pins. Verify with r3_verify.py"
  echo "    IMMEDIATELY: this would disprove r_3(212) <= 43."
fi
