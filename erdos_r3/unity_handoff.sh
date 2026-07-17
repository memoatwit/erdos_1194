#!/usr/bin/env bash
# Hand-off script for the r_3(212) = 43 upper-bound proof campaign on Unity.
# Pasteable in three sections.  Each section can be run independently.
#
#   Section A — one-time env setup on Unity (run via SSH after first login).
#   Section B — rsync from laptop to Unity (run on the laptop).
#   Section C — submit Phase 1 + Phase 2 on Unity.
#
# Adjust LOCAL_REPO and UNITY_USER if your paths differ.

set -euo pipefail

###############################################################################
# Section A.  ONE-TIME UNITY SETUP — run this on Unity after first SSH.
###############################################################################
# ssh ergezerm_wit_edu@unity.rc.umass.edu
#
# Then paste:
#
#   set -euo pipefail
#   mkdir -p ~/erdos_r3/results/slurm_logs ~/erdos_r3/results/broad24
#   cd ~/erdos_r3
#
#   # Try to find a conda module — name varies on Unity.
#   module avail conda 2>&1 | head -20
#   module load conda/latest 2>/dev/null \
#     || module load miniconda3/latest 2>/dev/null \
#     || module load anaconda3 2>/dev/null \
#     || echo "WARN: no conda module found; will fall back to system python"
#
#   # Create r3 env once.
#   if ! conda env list | grep -q '^r3 '; then
#     conda create -y -n r3 python=3.11
#   fi
#   source activate r3 || conda activate r3
#   pip install --quiet ortools numpy
#
#   # Sanity check.
#   python3 -c "from ortools.sat.python import cp_model as cp; \
#               from ortools.sat.python.cp_model import CpModel; \
#               m = CpModel(); print('ortools OK')"
#
#   # Confirm SLURM array limit.
#   scontrol show config 2>/dev/null | grep -i MaxArray || true

###############################################################################
# Section B.  RSYNC FROM LAPTOP TO UNITY — run on the laptop.
###############################################################################

LOCAL_REPO="${HOME}/Documents/GitHub/erdos_1194/erdos_r3"
UNITY_USER="ergezerm_wit_edu"
UNITY_HOST="unity.rc.umass.edu"
REMOTE="${UNITY_USER}@${UNITY_HOST}:~/erdos_r3"

# Python and markdown sources (exclude local caches and macOS-only .deps tree).
rsync -av --delete-excluded \
  --exclude '__pycache__/' \
  --exclude '.deps/' \
  --exclude 'results/' \
  --exclude '*.pyc' \
  "${LOCAL_REPO}/" "${REMOTE}/"

# Critical reference data: lower-bound witness, split-vars table, endpoint
# force file, and the broad-24 JSONL + chunk 191 partial.
rsync -av \
  "${LOCAL_REPO}/results/N212_K43_witness.json" \
  "${LOCAL_REPO}/results/N212_K43_witness_degree_order.json" \
  "${LOCAL_REPO}/results/N212_K44_force_endpoints.json" \
  "${LOCAL_REPO}/results/N212_K44_split_witness24_endpoints_pruned_600.jsonl" \
  "${LOCAL_REPO}/results/refine_N212_K44_witness24_chunk191_next16_60.jsonl" \
  "${REMOTE}/results/"

# Optional: previously closed refinements.  Uploading these lets the runner
# skip rerunning them.
for cid in 63 95 126 127 159 31 31_255; do
  src="${LOCAL_REPO}/results/refine_N212_K44_witness24_chunk${cid}_next"
  for depth in 8 16; do
    f="${src}${depth}_60.jsonl"
    [ -f "$f" ] && rsync -av "$f" "${REMOTE}/results/"
  done
done

echo
echo "Sync complete.  Now SSH to Unity:"
echo "    ssh ${UNITY_USER}@${UNITY_HOST}"
echo "and run Section C below."

###############################################################################
# Section C.  SUBMIT ON UNITY — run on Unity after SSH.
###############################################################################
# ssh ergezerm_wit_edu@unity.rc.umass.edu
#
# Then paste:
#
#   set -euo pipefail
#   cd ~/erdos_r3
#   source activate r3 || conda activate r3
#
#   # Verify the witness on Unity (cross-check the local verification).
#   python3 r3_verify.py results/N212_K43_witness.json
#
#   # ---- Phase 1: 15-task array closing the prefix [0..574] ----
#   python3 r3_slurm_emit.py --phase 1 \
#       --broad results/N212_K44_split_witness24_endpoints_pruned_600.jsonl \
#       --skip-closed "31,63,95,126,127,159" \
#       --out submit_phase1.sbatch
#   echo "--- submit_phase1.sbatch ---"
#   head -25 submit_phase1.sbatch
#   read -p "Looks good?  Press ENTER to submit, Ctrl+C to abort: "
#   PHASE1_JOB=$(sbatch --parsable submit_phase1.sbatch)
#   echo "Phase 1 job: $PHASE1_JOB"
#   squeue -j "$PHASE1_JOB"
#
#   # Wait for Phase 1 to finish, then verify all refinements closed.
#   # (Optional: have Phase 2 depend on Phase 1 with --dependency=afterok.)
#
#   # ---- Phase 2 calibration batch: 1000 chunks from 575 to 1574 ----
#   python3 r3_slurm_emit.py --phase 2 \
#       --chunk-start 575 --chunk-end 1575 \
#       --chunks-per-task 100 \
#       --out submit_phase2_575_1574.sbatch
#   echo "--- submit_phase2_575_1574.sbatch ---"
#   head -25 submit_phase2_575_1574.sbatch
#   read -p "Looks good?  Press ENTER to submit, Ctrl+C to abort: "
#   PHASE2_JOB=$(sbatch --parsable submit_phase2_575_1574.sbatch)
#   echo "Phase 2 job: $PHASE2_JOB"
#
#   # After Phase 2 completes, aggregate:
#   python3 r3_collect.py \
#       --shard-dir results/broad24 \
#       --chunk-start 575 --chunk-end 1575 \
#       --out results/N212_K44_broad24_575_1574.jsonl \
#       --missing-out results/N212_K44_missing_575_1574.txt \
#       --unknown-out results/N212_K44_unknown_575_1574.txt
#
#   # The aggregator prints a JSON summary including status_counts.
#   # If status_counts looks healthy (most INFEASIBLE, small UNKNOWN tail),
#   # scale up the next Phase 2 batch.
#
# To run beyond 1575 in larger batches once calibration succeeds:
#
#   python3 r3_slurm_emit.py --phase 2 \
#       --chunk-start 1575 --chunk-end 11575 \
#       --chunks-per-task 250 \
#       --array-throttle 500 \
#       --out submit_phase2_1575_11574.sbatch
#   sbatch submit_phase2_1575_11574.sbatch
#
# Adjust --array-throttle, --chunk-time-limit, --cpus, --mem, --partition
# based on Unity's observed behavior.
