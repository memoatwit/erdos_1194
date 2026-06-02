# Cluster strategy for r_3(212) = 43 proof

## Resources

- Unity HPC at UMass: `unity.rc.umass.edu`, user `ergezerm_wit_edu`.
- SLURM scheduler (assumed; confirm at first login).
- Per-node assumptions to verify: cores per node, RAM, time wall, queue limits.

## What changes from the laptop calculus

The laptop scaling for the broad-24 sweep:

| compute | mean 44s/chunk | median 6.7s/chunk |
|---|---|---|
| 1 core | 17.5 yr | 2.7 yr |
| 16 cores | 1.1 yr | 60 days |

On Unity with 500-1000 allocated cores, the median-case finish is 1-2 days
and even the worst-case mean is 1-2 weeks.  **The broad-24 sweep is
realistically completable as a cluster campaign.**

The remaining 14+1 unknown refinements from rows 0..574 are trivial at
cluster scale — they fit in a few hours of node time at most.

## Plan in three phases

### Phase 1: Close the prefix (0..574)

Goal: every UNKNOWN chunk in the existing broad-24 JSONL is resolved.

- Use the existing `r3_proof_manager.py` to enumerate refinement commands.
- Submit each refinement as one Slurm task (or as elements of a job array).
- Expected wall time: hours.
- Win condition for the phase: the broad-24 prefix JSONL has zero UNKNOWN
  rows AND every refinement file has zero UNKNOWN rows.

### Phase 2: Sweep the rest of broad-24

Goal: enumerate broad-24 chunks 575..12,582,911.

- Use SLURM array jobs, one task per chunk.  Each task runs the equivalent
  range of chunk IDs, not one task per chunk.  Each task runs
  `r3_split_cpsat.py` at depth 24 with the established split variables,
  endpoint forcing, AP-pruning, and a 600 s cap per chunk.
- Output: one JSONL shard per array task, usually named
  `results/broad24/chunks_START_END.jsonl`.  Shards may contain many chunk
  rows; collect them after the array completes.
- Job array size: choose the chunk range and `--chunks-per-task` so the array
  fits Unity queue limits.  A calibration batch like 1000 chunks with
  `--chunks-per-task 100` is a good first scale test.
- Win condition for the phase: every chunk_id in [0, 12,582,912) is logged
  as INFEASIBLE (or fed to Phase 3).

### Phase 3: Refine any UNKNOWNs from Phase 2

Same loop as Phase 1, scaled up.  Most Phase-2 chunks will close inside the
600 s cap; the tail of UNKNOWNs gets a depth-16 refinement, and any
remaining unknowns from that get a depth-8 refinement.

If at any point a FEASIBLE row appears, stop — r_3(212) >= 44 and the OEIS
table is wrong, which is itself a real result.

## Engineering bits to add before the first Unity submit

1. `r3_slurm_emit.py` — generate SBATCH array job scripts.
   - Input: chunk-id range, depth, split vars, fix-in, hint, wall, output dir.
   - Output: a `.sbatch` script + helper that runs one chunk range per
     SLURM_ARRAY_TASK_ID.
2. Per-task output shard (not a shared JSONL).  Avoids file-lock contention.
   Concatenate after the array completes.
3. Robust resume: a tiny `r3_collect.py` that scans `results/broad24/*.jsonl`,
   builds the master JSONL, and lists chunk_ids still missing.
4. Light environment setup: a `setup_unity.sh` that creates a Python
   venv or conda env with `ortools` and copies the working `.deps` if
   prebuilt for the Unity Linux.

## Notes on validity

For the proof to be water-tight after the campaign:

- Conditional pruning (`global_fixed_in = {1, 212}`) requires
  `r_3(211) = 43`.  Either cite OEIS A003002 and Cariboni's b-file, or
  redo `r_3(211)` exactly on the cluster (a much smaller campaign).
- The 43-witness has been verified locally; verify again on Unity with the
  same `r3_verify.py` to remove any ABI-mismatch concern.
- The complete JSONL should be archived plus the witness JSON and the
  OEIS-ready triple `(212, 43, [witness])`.

## Open questions for the user

- What's the typical job array size limit on Unity?
- Any storage quota concerns? 12.58M JSONL lines at ~1 KB each = ~12 GB raw.
  Concatenated probably more.
- Preferred Python env on Unity?  miniconda module, system Python 3.11+,
  or self-built venv?
