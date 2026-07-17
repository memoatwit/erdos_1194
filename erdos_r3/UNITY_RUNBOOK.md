# Unity SLURM Runbook for the r_3(212) upper-bound campaign

Step-by-step for running the upper-bound proof campaign on the UMass Unity
cluster.

## 0. SSH setup

```bash
ssh ergezerm_wit_edu@unity.rc.umass.edu
```

(Uses the IdentityFile already configured: `~/.ssh/privkey.key`.)

## 1. One-time environment setup on Unity

Create the working directory and a conda env with `ortools` and `numpy`.

```bash
mkdir -p ~/erdos_r3/results
cd ~/erdos_r3

# Load conda module (name may vary on Unity; try a few):
module load conda/latest 2>/dev/null || module load miniconda/latest || module load anaconda3

conda create -n r3 python=3.11 -y
conda activate r3
pip install ortools

# Sanity:
python3 -c "from ortools.sat.python import cp_model; print('OK', cp_model.CpSolver())"
```

## 2. Upload the local working tree

From your laptop:

```bash
LOCAL=~/Documents/GitHub/erdos_1194/erdos_r3
RDIR=ergezerm_wit_edu@unity.rc.umass.edu:~/erdos_r3

# Source files
rsync -av --exclude '.deps' --exclude '__pycache__' \
    "$LOCAL/"*.py "$LOCAL/"*.md \
    "$RDIR/"

# Reference data
rsync -av "$LOCAL/results/N212_K43_witness.json" \
          "$LOCAL/results/N212_K43_witness_degree_order.json" \
          "$LOCAL/results/N212_K44_force_endpoints.json" \
          "$LOCAL/results/N212_K44_split_witness24_endpoints_pruned_600.jsonl" \
          "$LOCAL/results/refine_N212_K44_witness24_chunk191_next16_60.jsonl" \
          "$RDIR/results/"

# Optional: existing closed refinements (so the runner skips them)
rsync -av "$LOCAL/results/refine_N212_K44_witness24_chunk63_next16_60.jsonl" \
          "$LOCAL/results/refine_N212_K44_witness24_chunk95_next16_60.jsonl" \
          "$LOCAL/results/refine_N212_K44_witness24_chunk126_next16_60.jsonl" \
          "$LOCAL/results/refine_N212_K44_witness24_chunk127_next16_60.jsonl" \
          "$LOCAL/results/refine_N212_K44_witness24_chunk159_next16_60.jsonl" \
          "$RDIR/results/"
```

## 3. Phase 1 (close the prefix)

```bash
cd ~/erdos_r3
python3 r3_slurm_emit.py --phase 1 \
    --broad results/N212_K44_split_witness24_endpoints_pruned_600.jsonl \
    --skip-closed "31,63,95,126,127,159" \
    --out submit_phase1.sbatch

# Inspect:
less submit_phase1.sbatch

# Submit:
sbatch submit_phase1.sbatch
```

Monitor:

```bash
squeue -u $USER
tail -f results/slurm_logs/phase1-<JOB_ID>_<TASK_ID>.out
```

Phase 1 finishes when all 15 refinement files have ~27,648 rows
(or fewer if AP-pruning makes them smaller), all INFEASIBLE.  Confirm:

```bash
python3 -c "
import json, glob
for fn in sorted(glob.glob('results/refine_N212_K44_witness24_chunk*_next16_60.jsonl')):
    rows = [json.loads(l) for l in open(fn)]
    statuses = {}
    for r in rows: statuses[r.get('status', '?')] = statuses.get(r.get('status', '?'), 0) + 1
    print(f'{fn}: {len(rows)} rows, {statuses}')
"
```

If any UNKNOWN remains: refine further with depth 8.

## 4. Phase 2 (broad-24 sweep)

Start with a 1000-chunk batch to calibrate.  If most close in <60 s, scale up.
Phase-2 jobs use contiguous chunk ranges per SLURM task (`--chunks-per-task`)
instead of one array task per chunk; this avoids paying the broad-24 iterator
startup cost millions of times.

```bash
python3 r3_slurm_emit.py --phase 2 \
    --chunk-start 575 --chunk-end 1575 \
    --chunks-per-task 100 \
    --out submit_phase2_575_1574.sbatch
sbatch submit_phase2_575_1574.sbatch
```

After array completes:

```bash
python3 r3_collect.py \
    --shard-dir results/broad24 \
    --chunk-start 575 --chunk-end 1575 \
    --out results/N212_K44_broad24_575_1574.jsonl \
    --missing-out results/N212_K44_missing_575_1574.txt \
    --unknown-out results/N212_K44_unknown_575_1574.txt
```

If status counts look healthy (mostly INFEASIBLE, <5% UNKNOWN), submit
larger batches.  The number of array tasks is approximately
`ceil((chunk_end - chunk_start) / chunks_per_task)`, so tune
`--chunks-per-task` together with Unity's array task limit
(`scontrol show config | grep -i MaxArray`).

## 5. Phase 3 (refine Phase 2 UNKNOWNs)

For each chunk_id in `N212_K44_unknown_*.txt`, submit a refinement task.
This can be a small array job similar to Phase 1.  Template:

```bash
# After Phase 2 has produced unknown lists, batch them:
awk 'BEGIN{n=0} {ids = ids $0 " "; n++} END { print "TASKS=(" ids ")"; print "N=" n }' \
    results/N212_K44_unknown_*.txt > phase3_tasks.sh
```

(Same pattern as Phase 1: array job with embedded `TASKS=(...)` table.)

## 6. Win condition

The proof of `r_3(212) = 43` requires:

1. The 43-point witness verifies.  ✓ (already saved).
2. EVERY chunk in [0, 12,582,912) ultimately resolves as INFEASIBLE
   (either at depth 24, depth 24+16, depth 24+16+8, etc.).
3. The `r_3(211) = 43` premise (used by the `1, 212 ∈ A` forcing) is cited
   from OEIS A003002 or independently certified.

If at any point a chunk closes as FEASIBLE: stop — you have a 44-point set
proving `r_3(212) >= 44`, which is even bigger news (it contradicts the
expected OEIS continuation).

## Troubleshooting

* "ImportError: numpy._core" → conda env was created against a different
  numpy ABI.  Recreate the env from scratch.
* SLURM array exceeds MaxArraySize → split the range into multiple
  submissions.
* Many UNKNOWNs at 60 s wall → bump `--chunk-time-limit` on the next batch.
* Storage filling up → `tar -czf broad24_shards_*.tar.gz` periodically.
