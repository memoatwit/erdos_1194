# Session Handoff: Erdős `r_3(212)` Exact-Value Attempt

Checkpoint date: May 20, 2026

## Goal

Prove the next OEIS-frontier value

```text
r_3(212) = 43.
```

We already have a verified 43-point AP-free witness in `[1,212]`, so the
remaining upper-bound task is to prove that no 44-point 3-AP-free subset of
`[1,212]` exists.

Important conditional pruning fact used by the search:

```text
If r_3(211)=43, then any 44-set in [1,212] must contain both 1 and 212.
```

Reason: if a 44-set omits `212`, it lies in `[1,211]`; if it omits `1`, subtract
1 from every element to get a 44-set in `[1,211]`.  This is encoded in
`results/N212_K44_force_endpoints.json`.

For a fully self-contained proof, the `r_3(211)=43` input should either be
cited/accepted from OEIS A003002 or independently certified.

## Current Bottom Line

The proof is not complete yet.

Current evidence strongly supports the target:

- Verified lower bound: a 43-point witness for `N=212`.
- A 600-second greedy probe found no 44-set at `N=212`.
- The CP-SAT upper-bound search is now producing real certificate pieces.
- The first 575 depth-24 witness-split base chunks were processed:
  - `554` were `INFEASIBLE`.
  - `21` were `UNKNOWN` at the 600s chunk cap.
- Several `UNKNOWN` base chunks have now been closed by recursive refinement.

The big discovery from this session is that broad central-degree splitting is
bad, but witness-variable splitting plus recursive refinement is good.

## Implemented Tools

### `r3_cpsat.py`

Added:

- `--fix-in PATH`
- `--fix-out PATH`
- `--hint PATH`
- `--save-full PATH`
- `--branch-order {natural,degree,reverse-degree}`
- `--branch-value {max,min}`
- `--fixed-search`

Decision mode uses `sum == K`, not `sum >= K`.

### `r3_random_greedy.py`

Randomized lower-bound/repair search.

Used successfully to save the 43-point witness:

```text
results/N212_K43_witness.json
```

Also ran a 600s `N=212,K=44` probe:

```text
results/N212_K44_greedy_probe.json
```

Result: `found=false`.

### `r3_split_cpsat.py`

Resumable JSONL split runner.

Important features added:

- endpoint-pair splitting,
- degree-variable splitting,
- explicit split variables via `--split-vars`,
- global fixed variables via `--fix-in` / `--fix-out`,
- refinement of a prior JSONL chunk via `--base-jsonl` / `--base-chunk-id`,
- AP-prefix pruning with `--prune-prefix-ap`,
- quiet durable logging via `--quiet --progress-every N`,
- CP-SAT branch controls passed through to `r3_cpsat.py`.

### `r3_bb.py`

Experimental exact branch-and-bound fallback.

It passed small smoke tests but is not yet frontier-grade.  CP-SAT split/refine
is currently the productive path.

## Verified Witness

Saved at:

```text
erdos_r3/results/N212_K43_witness.json
```

Witness:

```text
[3, 4, 9, 11, 12, 16, 22, 24, 25, 27, 31, 48, 52, 54, 55, 57, 63, 67, 68, 70, 75, 76, 91, 142, 145, 150, 152, 156, 161, 164, 165, 168, 181, 182, 187, 189, 190, 195, 202, 204, 205, 207, 211]
```

Verify with:

```bash
python3 erdos_r3/r3_verify.py erdos_r3/results/N212_K43_witness.json
```

## Python Environment Warning

Use:

```bash
/Users/memo/miniconda3/bin/python3
```

or the normal login-shell `python3` that resolves to that path.

Do not run long `bash -lc` loops that accidentally use Apple Python 3.9.  The
local `ortools`/`numpy` dependency in `erdos_r3/.deps` is built for Python 3.11,
and Apple Python 3.9 fails with a NumPy C-extension import error.

## Search Strategy That Worked

The useful split variables are the known 43-witness values, ordered by AP
incidence:

```text
results/N212_K43_witness_degree_order.json
```

The broad depth-24 run command was:

```bash
/Users/memo/miniconda3/bin/python3 erdos_r3/r3_split_cpsat.py \
  --N 212 --K 44 \
  --pairs 24 \
  --strategy degree-vars \
  --split-count 24 \
  --split-vars erdos_r3/results/N212_K43_witness_degree_order.json \
  --chunk-time-limit 600 \
  --workers-per-chunk 8 \
  --hint erdos_r3/results/N212_K43_witness.json \
  --fix-in erdos_r3/results/N212_K44_force_endpoints.json \
  --prune-prefix-ap \
  --branch-order degree \
  --branch-value min \
  --fixed-search \
  --quiet \
  --progress-every 1000 \
  --output erdos_r3/results/N212_K44_split_witness24_endpoints_pruned_600.jsonl
```

This runner is resumable by chunk id.  It will skip rows already present in the
output JSONL.

## Broad Depth-24 Checkpoint

File:

```text
results/N212_K44_split_witness24_endpoints_pruned_600.jsonl
```

Current rows:

```text
575 rows total
554 INFEASIBLE
21 UNKNOWN
processed chunk IDs: 0..574
```

Unknown base chunks from that file:

```text
31, 63, 95, 126, 127, 159, 191, 223, 254, 255,
319, 351, 367, 382, 383, 415, 447, 479, 495, 510, 511
```

Important: this is only an initial prefix of the full depth-24 split tree.
Counting showed about `12,582,912` AP-pruned depth-24 leaves.  The full proof
requires either processing/resuming the broad tree or replacing it with a
smarter adaptive manager.

## Refinement Status

Refinement command template:

```bash
/Users/memo/miniconda3/bin/python3 erdos_r3/r3_split_cpsat.py \
  --N 212 --K 44 \
  --pairs 16 \
  --strategy degree-vars \
  --split-count 16 \
  --split-vars erdos_r3/results/N212_K43_witness_degree_order.json \
  --base-jsonl erdos_r3/results/N212_K44_split_witness24_endpoints_pruned_600.jsonl \
  --base-chunk-id CHUNK_ID \
  --chunk-time-limit 60 \
  --workers-per-chunk 8 \
  --hint erdos_r3/results/N212_K43_witness.json \
  --prune-prefix-ap \
  --branch-order degree \
  --branch-value min \
  --fixed-search \
  --quiet \
  --progress-every 5000 \
  --output erdos_r3/results/refine_N212_K44_witness24_chunkCHUNK_ID_next16_60.jsonl
```

Closed refinements:

```text
base chunk 31:
  First refinement file: 255 INFEASIBLE, 1 UNKNOWN.
  Second refinement of subchunk 255: 256 INFEASIBLE.
  Net status: CLOSED.

base chunk 63:
  27,648 INFEASIBLE, 0 UNKNOWN.

base chunk 95:
  27,648 INFEASIBLE, 0 UNKNOWN.

base chunk 126:
  27,648 INFEASIBLE, 0 UNKNOWN.

base chunk 127:
  27,648 INFEASIBLE, 0 UNKNOWN.

base chunk 159:
  27,648 INFEASIBLE, 0 UNKNOWN.
```

Partial refinement:

```text
base chunk 191:
  12,107 INFEASIBLE so far when the process was stopped for this handoff.
  Resume the same command; the runner will skip existing chunk ids.
```

Not yet refined:

```text
223, 254, 255, 319, 351, 367, 382, 383,
415, 447, 479, 495, 510, 511
```

No feasible 44-set has appeared in any CP-SAT run.

## Recommended Next Move

1. Resume and finish refinement of base chunk `191`.
2. Refine the remaining base unknowns:

```text
223, 254, 255, 319, 351, 367, 382, 383,
415, 447, 479, 495, 510, 511
```

3. Once all known base unknowns from rows `0..574` are closed, resume the broad
   depth-24 run from the same JSONL.
4. Whenever a new broad chunk hits `UNKNOWN`, stop the broad run and refine that
   chunk by the next witness variables.

The manual loop works, but the obvious next engineering improvement is an
adaptive proof manager:

- run broad depth-24 chunks,
- detect `UNKNOWN`,
- refine that base chunk to depth +16,
- if a refined subchunk is still `UNKNOWN`, refine again,
- keep a manifest of closed base chunks,
- stop immediately on `FEASIBLE`.

That manager would turn the current successful manual pattern into a robust
overnight proof pipeline.

## Current Process State

No `N=212,K=44` split-proof process is intentionally left running at this
checkpoint.

The last active loop was stopped after base chunk `159` fully closed and base
chunk `191` had a partial refinement file.

## Cluster artifacts added in the next session (May 20 PM)

User confirmed access to Unity HPC (`unity.rc.umass.edu`, user
`ergezerm_wit_edu`).  With ~500-1000 parallel cores, the broad-24 sweep
goes from infeasible (1+ year 16-way) to plausible (1-2 weeks wall).

The following are now in `erdos_r3/`:

- `r3_proof_manager.py` — adaptive proof manager.  Parses any broad JSONL,
  classifies UNKNOWN chunks as closed/partial/fresh, emits per-chunk
  refinement commands, supports two-level (depth 16 + depth 8) refinement
  and optional in-process subprocess execution.
- `r3_split_cpsat.py` — added `--only-chunk-id N` for single-chunk smoke
  runs and `--chunk-id-start/--chunk-id-end` for SLURM range tasks.  Use
  range tasks for Phase 2; one task per chunk wastes too much iterator
  overhead at cluster scale.
- `r3_slurm_emit.py` — SBATCH array generator.  Phase 1 = refinement queue
  for unknown base chunks, Phase 2 = broad-24 sweep over `[start, end)` with
  configurable `--chunks-per-task`.
  Default account/partition/wall configurable via CLI; throttle %200 by
  default.
- `r3_collect.py` — Phase 2 shard aggregator.  Builds master JSONL,
  reports status histogram, lists missing/UNKNOWN chunk IDs.
- `unity_handoff.sh` — single pasteable script: section A (Unity env
  setup), section B (laptop rsync), section C (Unity submit + monitor).
- `UNITY_RUNBOOK.md` — full step-by-step runbook with phases 1/2/3 and
  troubleshooting.
- `cluster_strategy.md` — strategic overview, scaling table, phase plan.

Immediate next move when resources permit: paste `unity_handoff.sh`
Section A on Unity, Section B on laptop, Section C on Unity.  Phase 1
should close the prefix `[0..574]` in roughly an hour of node time.
After Phase 1, calibrate with a 1k Phase-2 batch (chunks 575-1574,
for example `--chunks-per-task 100`),
inspect the timing histogram, scale up.

The proof completes when:

1. Every chunk in `[0, 12,582,912)` is logged as INFEASIBLE through
   broad-24 or recursive refinement.
2. The 43-witness is reverified on Unity with `r3_verify.py`.
3. The `r_3(211) = 43` premise is cited (OEIS A003002, Cariboni's b-file)
   or independently certified.

If any chunk closes as FEASIBLE, stop — that is a 44-point 3-AP-free set
in `[1,212]`, contradicting the expected continuation of OEIS A003002.

## Unity submission status (May 20 early AM)

Codex connected to Unity with:

```bash
ssh -i ~/.ssh/privkey.key ergezerm_wit_edu@unity.rc.umass.edu
```

Important site-specific corrections:

- Use the existing Python prefix directly:
  `/work/pi_ergezerm_wit_edu/ergezerm_wit_edu-conda/envs/soft/bin/python`.
  The user's `.condarc` currently has duplicate `envs_dirs` entries, so
  `conda activate` is brittle.
- `ortools==9.15.6755` was installed into that prefix and verified.
  Note: pip upgraded `numpy`, `pandas`, and `protobuf` in the shared `soft`
  environment, so avoid using this env for unrelated ML/audio work without
  checking dependencies first.
- Valid SLURM account is `pi_ergezerm_wit_edu`; `ergezerm_wit_edu` was
  rejected as an account.  Partition `cpu` works.
- `r3_slurm_emit.py` was patched so future `#SBATCH --output/--error`
  paths use relative `results/slurm_logs/...`; SLURM did not expand `$HOME`
  inside SBATCH directives.
- `r3_slurm_emit.py` was also patched so future Phase 2 jobs write each
  shard to `*.tmp_${SLURM_JOB_ID}_${SLURM_ARRAY_TASK_ID}` and `mv` it to the
  final shard path only after successful completion.  This avoids treating a
  timed-out partial shard as resumable output.

Submitted jobs:

- Phase 1 prefix refinement array: job `57957119`, 15 tasks:
  `191, 223, 254, 255, 319, 351, 367, 382, 383, 415, 447, 479, 495, 510, 511`.
  Completed: all 15 refinement files have exactly `27648` rows, all
  `INFEASIBLE`, with no `FEASIBLE` rows.  This closes the original prefix
  `[0..574]`.
- Phase 2 calibration array: job `57957184`, chunks `[575,1575)`,
  `--chunks-per-task 100`, 10 tasks total.  Completed and collected to
  `results/N212_K44_broad24_575_1574.jsonl`: `1000` rows, `799`
  `INFEASIBLE`, `201` `UNKNOWN`, `0` `FEASIBLE`.
- Calibration refinement array: job `57961973`, 201 tasks, one for each
  `UNKNOWN` in `results/N212_K44_broad24_575_1574.jsonl`, throttled at
  `%100` (about 800 CPUs max).  Completed/left queue.
- Base chunk `1021` initially looked incomplete because it had `18432` rows
  instead of the common `27648`.  Single resume job `57983585` processed
  `0` new rows, proving that the pruned depth-16 assignment space for this
  base chunk has only `18432` generated subchunks.  Treat it as closed.
- Final calibration refinement result: `201/201` originally unknown broad
  chunks closed at depth 16.  Across all calibration refinement rows:
  `5,548,032` `INFEASIBLE`, `0` `UNKNOWN`, `0` `FEASIBLE`.
- Next bounded broad Phase-2 batch submitted: job `57983894`, chunks
  `[1575,11575)`, `10,000` chunks total, `--chunks-per-task 250`, array
  size `40`, throttle `%75`.  This is a bounded expansion, not the full
  12.5M sweep.
- Job `57983894` left the queue with `31/40` final shards written.  Nine
  array tasks hit the 2-hour wall and left temp shards:
  `[2825,3075)`, `[4825,5075)`, `[5575,5825)`, `[5825,6075)`,
  `[6825,7075)`, `[7575,7825)`, `[7825,8075)`, `[8075,8325)`,
  `[9075,9325)`.  Error logs explicitly say `DUE TO TIME LIMIT`.
- Retried those nine ranges with smaller Phase-2 shard tasks:
  `--chunks-per-task 50`, five array tasks per 250-chunk range.  Retry job
  IDs: `57985944` (`2825-3074`), `57985945` (`4825-5074`), `57985946`
  (`5575-5824`), `57985947` (`5825-6074`), `57985948` (`6825-7074`),
  `57985949` (`7575-7824`), `57985950` (`7825-8074`), `57985951`
  (`8075-8324`), `57985952` (`9075-9324`).  Several were running at the
  last check; others pending for priority.
- Retry jobs completed and final shards now cover all `10,000` chunks in
  `[1575,11575)`.  Collected to
  `results/N212_K44_broad24_1575_11574.jsonl`: `6967` `INFEASIBLE`,
  `3033` `UNKNOWN`, `0` `FEASIBLE`.
- Attempting one refinement array for all `3033` unknown chunks failed with
  `QOSMaxSubmitJobPerUserLimit`.  Unity QOS check showed `normal` has
  `MaxSubmitJobsPerUser=2000` and `MaxJobsPerUser=1000`, so refinement tails
  need to be split into smaller tranches.
- First refinement tranche submitted: job `57994277`, input
  `results/N212_K44_broad24_1575_11574_unknowns_0000_0999.jsonl`,
  `1000` unknown broad chunks, array `0-999%75`.  Remaining unknowns from
  the 10k batch still need later tranches after this one advances/completes.

## Window-bound pruning A/B pivot (May 21)

The 10k broad batch showed the 60s broad UNKNOWN rate rising to `30.3%`
(`3033/10000`).  Even though depth-16 refinement works mechanically, this
rate makes the full brute-force campaign too expensive if it persists.  The
next strategy is structural pruning via OEIS window-cardinality bounds.

Local/Unity code state:

- `r3_cpsat.py` supports `--window-bounds PATH` and adds interval constraints
  `sum(A ∩ [a,a+L-1]) <= r_3(L)` from `results/b003002.txt`.
- `r3_split_cpsat.py` passes those bounds into each CP-SAT solve.
- `r3_slurm_emit.py` now includes `--window-bounds "$workdir/results/b003002.txt"`
  in both Phase-1 and Phase-2 templates.
- `r3_slurm_emit.py` also now has `--shard-dir` so A/B runs can write to a
  clean shard directory instead of skipping existing `results/broad24` shards.
- Unity smoke check confirmed `window_constraints=22154` for `N=212,K=44`.

A/B job submitted:

- Job `57994460`
- Range `[575,675)` (`100` broad chunks)
- `--chunks-per-task 50`, array size `2`
- Shard directory: `results/broad24_window_ab_575_674`
- This job compares against the old broad result for the same range, which is
  already present in `results/broad24/chunks_00000575_00000674.jsonl`.
- Completed and collected to
  `results/N212_K44_broad24_window_ab_575_674.jsonl`.

A/B result:

| Run | Rows | INFEASIBLE | UNKNOWN | FEASIBLE | UNKNOWN rate | Sum solver seconds |
|---|---:|---:|---:|---:|---:|---:|
| old broad | 100 | 73 | 27 | 0 | 27% | 2386.543 |
| window-bounds | 100 | 100 | 0 | 0 | 0% | 108.475 |

This is a strong positive signal: window-cardinality constraints eliminated
the broad UNKNOWNs on this sample and reduced total solve time.  Next
step executed: cancel the old brute-tail refinement job and run a larger
window-bound batch on the same `[1575,11575)` range as the old 10k batch.

Old brute-tail job:

- Job `57994277` was cancelled with `scancel` after the A/B result.  It was
  still using about `600` running CPUs on the pre-window refinement path.
  Some completed refinement files remain valid, but this path is no longer
  the priority.

Window-bound 10k batch:

- Job `57994932`
- Range `[1575,11575)` (`10,000` broad chunks)
- `--chunks-per-task 50`, array size `200`, throttle `%75`
- Shard directory: `results/broad24_window_1575_11574`
- Submit script: `submit_phase2_window_1575_11574.sbatch`
- Running at last check: `32` tasks running, remaining tasks pending by
  priority.
- Completed and collected to
  `results/N212_K44_broad24_window_1575_11574.jsonl`.

10k old-vs-window comparison:

| Run | Rows | INFEASIBLE | UNKNOWN | FEASIBLE | UNKNOWN rate | Sum solver seconds |
|---|---:|---:|---:|---:|---:|---:|
| old broad | 10000 | 6967 | 3033 | 0 | 30.33% | 254158.071 |
| window-bounds | 10000 | 9835 | 165 | 0 | 1.65% | 35570.281 |

This is a decisive improvement.  Window constraints reduce broad UNKNOWN rate
by about `18.4x` on this 10k range and reduce total solver seconds by about
`7.1x`.  No `FEASIBLE` rows appeared.

Recommended next move: run a `100k` window-bound batch, not the full 12.5M
sweep yet.  Use isolated shard dir, e.g. `results/broad24_window_11575_111574`,
and keep `--chunks-per-task 50` unless queue overhead becomes a problem.

100k window-bound batch submitted:

- Job `57997994`
- Range `[11575,111575)` (`100,000` broad chunks)
- `--chunks-per-task 50`, array size `2000`, throttle `%75`
- Shard directory: `results/broad24_window_11575_111574`
- Submit script: `submit_phase2_window_11575_111574.sbatch`
- Accepted by SLURM; pending at first check.

Job `57997994` completed and was collected on May 21, 2026:

```text
results/N212_K44_broad24_window_11575_111574.jsonl

range: [11575, 111575)
rows: 100,000
INFEASIBLE: 93,929
UNKNOWN: 6,071
FEASIBLE: 0
UNKNOWN rate: 6.071%
```

This is still dramatically better than the old no-window broad search, but the
UNKNOWN rate increased from `1.65%` on the 10k window batch to `6.071%` on this
100k window batch.  Do not submit the full `12.5M` sweep yet.  Next best move is
to analyze the 6,071 UNKNOWN chunks, run a bounded depth-16 refinement sample,
and/or test whether a stronger structural pruning layer flattens this growth.

## Window 100k UNKNOWN Profiling

Added reusable profiler:

```text
r3_profile_unknowns.py
```

Profile output:

```text
results/N212_K44_window100k_unknown_profile.json
```

Key facts from the `[11575,111575)` 100k window-bound batch:

```text
rows: 100,000
INFEASIBLE: 93,929
UNKNOWN: 6,071
FEASIBLE: 0
UNKNOWN rate: 6.071%

INFEASIBLE seconds:
  median 1.6705
  p90 8.2867
  p99 40.7555
  mean 3.9118

UNKNOWN seconds:
  min 59.9909
  median 60.0264
  mean 60.0474
  max 60.3582
```

Interpretation: every UNKNOWN is a genuine 60s timeout.  This is not a mixed
bag of mildly slow chunks; the unresolved set is exactly the timeout tail.

The UNKNOWNs are pocketed rather than uniform.  The 20 equal-width 5k buckets
range from `1.64%` to `13.60%` UNKNOWN, with the worst bucket
`[61575,66575)` at `13.60%`.  The largest contiguous UNKNOWN run found in this
100k batch was length `27` at chunk IDs `98277..98303`; many other runs have
length around `15`.

The strongest split-variable enrichment signal is that several middle witness
pins being forced out makes UNKNOWNs much more likely:

```text
value 68: UNKNOWN if in 2.40%, if out 9.75%
value 75: UNKNOWN if in 2.42%, if out 9.72%
value 70: UNKNOWN if in 2.45%, if out 9.69%
value 76: UNKNOWN if in 2.58%, if out 9.56%
value 91: UNKNOWN if in 2.73%, if out 9.42%
```

This suggests a structured hard pocket, not random noise.

## Window 100k Depth-16 Refinement Sample

Sample file:

```text
results/N212_K44_window100k_refine_sample100.json
```

Sampling rule: 100 UNKNOWN base chunks total, with the 20 slowest UNKNOWN chunks
first and the remaining 80 chosen reproducibly at random with seed `1194`.

Added phase-1 emitter support for this:

```text
r3_slurm_emit.py --chunk-list PATH --limit-unknowns N --refine-prefix PREFIX
```

Submitted Unity refinement sample:

```text
job: 58144128
base JSONL: results/N212_K44_broad24_window_11575_111574.jsonl
chunk list: results/N212_K44_window100k_refine_sample100.json
task count: 100
array throttle: %50
per task: depth-16, window-bounds, 60s subchunk cap, 8 workers
output pattern: results/refine_N212_K44_window100k_sample100_chunk*_next16_60.jsonl
submit script: submit_refine_window100k_sample100.sbatch
```

Monitor:

```bash
squeue -j 58144128
ls -lh ~/erdos_r3/results/refine_N212_K44_window100k_sample100_chunk*_next16_60.jsonl
grep -R -m 1 '"status": "FEASIBLE"' ~/erdos_r3/results/refine_N212_K44_window100k_sample100_chunk*_next16_60.jsonl
```

Completion result for job `58144128`:

```text
files: 100
row-level INFEASIBLE: 299,374
row-level UNKNOWN: 1
row-level FEASIBLE: 0
solver seconds sum: 168,502.785
median solver seconds per sampled base chunk: 1,615.748
row count range per sampled base chunk: 2,478..5,277
```

Interpretation: the 100-sample depth-16 refinement is highly encouraging but
not a clean full closure.  It closed `99/100` sampled base chunks and left one
residual UNKNOWN:

```text
base chunk: 106495
refinement output: results/refine_N212_K44_window100k_sample100_chunk106495_next16_60.jsonl
residual refinement chunk_id: 1535
FEASIBLE: 0
```

This keeps the broad+refine path alive, but it is not cheap enough to launch the
full 12.5M broad sweep blindly.  Next best move is a second-level refinement of
the single residual UNKNOWN, plus a larger or more targeted refinement sample
from the hard buckets before committing to campaign-scale compute.

Second-level residual refinement completed:

```text
job: 58151167
input: results/refine_N212_K44_window100k_sample100_chunk106495_next16_60.jsonl
base chunk within input: 1535
output: results/refine_N212_K44_window100k_sample100_chunk106495_sub1535_next8_60.jsonl

rows: 8
INFEASIBLE: 8
UNKNOWN: 0
FEASIBLE: 0
solver seconds sum: 56.531
```

The full 100-chunk refinement sample is therefore closed: all `100/100` sampled
100k-batch UNKNOWN base chunks now certify INFEASIBLE after depth-16 plus one
tiny depth-8 tail.  This makes the broad+refine path technically viable, but the
measured depth-16 cost is still large enough that the next step should be a
larger targeted sample/cost model, not the full `12.5M` sweep.

## Window 100k Stratified 500-Chunk Refinement Sample

Built a harder 500-chunk sample from the `6,071` UNKNOWN chunks in the completed
100k window-bound batch:

```text
sample: results/N212_K44_window100k_refine_sample500_stratified.json
metadata: results/N212_K44_window100k_refine_sample500_stratified_meta.json
seed: 11940522
sample size: 500
```

Sampling rule:

```text
125 chunks from the longest contiguous UNKNOWN runs
270 chunks from the six worst 5k buckets by UNKNOWN rate
100 chunks with one of {68,75,70,76,91} forced out
5 uniform random fill chunks
```

The six hard buckets targeted were:

```text
[61575,66575):   680 UNKNOWNs, 13.60%
[101575,106575): 450 UNKNOWNs, 9.00%
[56575,61575):   446 UNKNOWNs, 8.92%
[96575,101575):  433 UNKNOWNs, 8.66%
[91575,96575):   419 UNKNOWNs, 8.38%
[46575,51575):   416 UNKNOWNs, 8.32%
```

Submitted Unity refinement sample:

```text
job: 58152757
base JSONL: results/N212_K44_broad24_window_11575_111574.jsonl
chunk list: results/N212_K44_window100k_refine_sample500_stratified.json
task count: 500
array throttle: %75
per task: depth-16, window-bounds, 60s subchunk cap, 8 workers
output pattern: results/refine_N212_K44_window100k_sample500_chunk*_next16_60.jsonl
submit script: submit_refine_window100k_sample500.sbatch
```

Monitor:

```bash
squeue -j 58152757
ls -lh ~/erdos_r3/results/refine_N212_K44_window100k_sample500_chunk*_next16_60.jsonl
grep -R -m 1 '"status": "FEASIBLE"' ~/erdos_r3/results/refine_N212_K44_window100k_sample500_chunk*_next16_60.jsonl
```

Implementation update:

```text
Added r3_tail_emit.py
```

This script parses residual `UNKNOWN` rows from completed depth-16 refinement
files and emits one depth-8 SLURM array task per residual subchunk.  It has an
`--expected-files 500` guard so it refuses to emit a tail job before the full
sample-500 array is complete.

Tail-emitter command to run after job `58152757` finishes:

```bash
cd ~/erdos_r3
/work/pi_ergezerm_wit_edu/ergezerm_wit_edu-conda/envs/soft/bin/python \
  r3_tail_emit.py \
  --input-glob "results/refine_N212_K44_window100k_sample500_chunk*_next16_60.jsonl" \
  --expected-files 500 \
  --out submit_tail_sample500_next8.sbatch
sbatch submit_tail_sample500_next8.sbatch
```

The guard was tested while only `375/500` sample files existed; it correctly
refused to emit:

```text
Expected 500 files ... found 375.
```

Current partial state at that check:

```text
files: 375/500
INFEASIBLE rows: 1,311,384
UNKNOWN rows: 10
FEASIBLE rows: 0

residual tails so far:
  base 65535: subchunks 1439, 1519, 1531, 1533, 1534, 1535
  base 90111: subchunk 1535
  base 98303: subchunks 1439, 1531, 1535
```

Decision after completion:

- If this targeted hard sample closes with zero or tiny residual UNKNOWN tails,
  estimate the full cost of closing all `6,071` UNKNOWNs from the 100k interval.
- If it leaves many residual UNKNOWNs, pause broad scaling and work on stronger
  pruning before consuming more Unity time.
- Any FEASIBLE row immediately falsifies the proposed `r_3(212)=43` upper bound.

Decision after completion:

- If the sample closes with near-zero residual UNKNOWNs, the broad+refine path is
  still viable but needs a careful cost model.
- If the sample leaves a substantial residual UNKNOWN tail, stop brute scaling
  and focus on stronger structural pruning.
- Any FEASIBLE row immediately falsifies the proposed `r_3(212)=43` upper bound
  and should be verified with `r3_verify.py`.

Collection command used:

```bash
cd ~/erdos_r3
/work/pi_ergezerm_wit_edu/ergezerm_wit_edu-conda/envs/soft/bin/python \
  r3_collect.py --shard-dir results/broad24_window_11575_111574 \
  --chunk-start 11575 --chunk-end 111575 \
  --out results/N212_K44_broad24_window_11575_111574.jsonl
```

Collection command used:

```bash
cd ~/erdos_r3
/work/pi_ergezerm_wit_edu/ergezerm_wit_edu-conda/envs/soft/bin/python \
  r3_collect.py --shard-dir results/broad24_window_1575_11574 \
  --chunk-start 1575 --chunk-end 11575 \
  --out results/N212_K44_broad24_window_1575_11574.jsonl
```

Then compare against the old 10k batch:

```bash
cd ~/erdos_r3
/work/pi_ergezerm_wit_edu/ergezerm_wit_edu-conda/envs/soft/bin/python - <<'PY'
import json
from collections import Counter
for label, path in [
    ("old", "results/N212_K44_broad24_1575_11574.jsonl"),
    ("window", "results/N212_K44_broad24_window_1575_11574.jsonl"),
]:
    c = Counter()
    with open(path) as f:
        for line in f:
            if line.strip():
                c[json.loads(line).get("status", "UNKNOWN")] += 1
    print(label, dict(c))
PY
```

Collection command used:

```bash
cd ~/erdos_r3
/work/pi_ergezerm_wit_edu/ergezerm_wit_edu-conda/envs/soft/bin/python \
  r3_collect.py --shard-dir results/broad24_window_ab_575_674 \
  --chunk-start 575 --chunk-end 675 \
  --out results/N212_K44_broad24_window_ab_575_674.jsonl
```

Then compare UNKNOWN rates:

```bash
cd ~/erdos_r3
/work/pi_ergezerm_wit_edu/ergezerm_wit_edu-conda/envs/soft/bin/python - <<'PY'
import json
from collections import Counter
for label, path in [
    ("old", "results/broad24/chunks_00000575_00000674.jsonl"),
    ("window", "results/N212_K44_broad24_window_ab_575_674.jsonl"),
]:
    c = Counter()
    with open(path) as f:
        for line in f:
            if line.strip():
                c[json.loads(line).get("status", "UNKNOWN")] += 1
    print(label, dict(c))
PY
```

Do not submit more full-sweep or brute-tail jobs until the window-bound 10k
batch result is known.  If it also has near-zero UNKNOWNs, the next scale step
should be a 100k window-bound batch, not depth-16 brute refinement.

Useful monitor commands:

```bash
squeue -j 57957119,57957184
squeue -j 57961973,57983585,57983894
squeue -j 57985944,57985945,57985946,57985947,57985948,57985949,57985950,57985951,57985952
squeue -j 57994277
squeue -j 57994460
squeue -j 57994932
squeue -j 57997994
ls -lh ~/erdos_r3/results/refine_N212_K44_witness24_chunk*_next16_60.jsonl
ls -lh ~/erdos_r3/results/broad24/chunks_*.jsonl
ls -lh ~/erdos_r3/results/broad24_window_1575_11574/chunks_*.jsonl
ls -lh ~/erdos_r3/results/broad24_window_11575_111574/chunks_*.jsonl
```

After the Phase 2 calibration finishes, collect it with:

```bash
cd ~/erdos_r3
/work/pi_ergezerm_wit_edu/ergezerm_wit_edu-conda/envs/soft/bin/python \
  r3_collect.py --shard-dir results/broad24 \
  --chunk-start 575 --chunk-end 1575 \
  --out results/N212_K44_broad24_575_1574.jsonl
```

After the 10k Phase-2 batch finishes, collect it with:

```bash
cd ~/erdos_r3
/work/pi_ergezerm_wit_edu/ergezerm_wit_edu-conda/envs/soft/bin/python \
  r3_collect.py --shard-dir results/broad24 \
  --chunk-start 1575 --chunk-end 11575 \
  --out results/N212_K44_broad24_1575_11574.jsonl
```

## 2026-05-22 sample-500 depth-16 result and tail job

The stratified sample-500 depth-16 refinement job `58152757` completed on
Unity.  Final aggregate across all 500 files:

- `INFEASIBLE`: 2,076,095
- `UNKNOWN`: 10
- `FEASIBLE`: 0

Summary file written on Unity:

```text
results/N212_K44_window100k_sample500_refine16_summary.json
```

The ten residual UNKNOWN rows are:

```text
base 65535 sub 1439
base 65535 sub 1519
base 65535 sub 1531
base 65535 sub 1533
base 65535 sub 1534
base 65535 sub 1535
base 90111 sub 1535
base 98303 sub 1439
base 98303 sub 1531
base 98303 sub 1535
```

Important implementation note: `r3_tail_emit.py` had an over-escaped default
filename regex and was fixed locally, then synced to Unity.  The corrected
regex is:

```python
r"chunk([0-9]+)_next[0-9]+_[0-9]+\.jsonl$"
```

The second-level depth-8 tail cleanup was emitted and submitted:

```text
submit_tail_sample500_next8.sbatch
job 58293829
```

Monitor:

```bash
squeue -j 58293829
ls -lh ~/erdos_r3/results/refine_N212_K44_window100k_sample500_tail8_base*_sub*_next8_60.jsonl
grep -R '"status": *"FEASIBLE"' ~/erdos_r3/results/refine_N212_K44_window100k_sample500_tail8_base*_sub*_next8_60.jsonl
```

If all 10 tail files finish with no FEASIBLE and no UNKNOWN rows, the
sample-500 diagnostic is fully closed.  If any tail row is FEASIBLE, verify the
witness immediately before submitting any further jobs.

## 2026-05-23 corrected diagnostics launch

Depth-8 tail job `58293829` finished with:

- `INFEASIBLE`: 68
- `UNKNOWN`: 8
- `FEASIBLE`: 0

The corrected multi-level `r3_tail_emit.py` was synced to Unity and used to
emit the eight-row level-3 cleanup:

```text
submit_tail_sample500_level3_next8.sbatch
job 58298039
array 0-7%8
```

Level-3 input residuals:

```text
parent base65535_sub1519 chunk 7
parent base65535_sub1533 chunk 3
parent base65535_sub1535 chunk 3
parent base65535_sub1535 chunk 5
parent base65535_sub1535 chunk 7
parent base98303_sub1535 chunk 3
parent base98303_sub1535 chunk 5
parent base98303_sub1535 chunk 7
```

The two worst-bucket A/B diagnostics were also submitted:

```text
reorder 60s A/B: job 58298047, shard dir results/broad24_window_reorder_ab_61575_66574
wall-time 300s A/B: job 58298048, shard dir results/broad24_window_walltime300_ab_61575_66574
```

Monitor:

```bash
squeue -j 58298039,58298047,58298048
grep -R '"status": *"FEASIBLE"' \
  ~/erdos_r3/results/refine_N212_K44_window100k_sample500_tail_level3_*_next8_60.jsonl \
  ~/erdos_r3/results/broad24_window_reorder_ab_61575_66574/*.jsonl \
  ~/erdos_r3/results/broad24_window_walltime300_ab_61575_66574/*.jsonl
```

Do not submit the full 12.5M sweep.  Any FEASIBLE row overrides the campaign:
extract and verify the witness immediately.

## 2026-05-23 corrected diagnostics results

Jobs `58298039`, `58298047`, and `58298048` all drained.  No FEASIBLE rows
appeared.

Level-3 tail cleanup `58298039`:

```text
files: 8
INFEASIBLE: 2
UNKNOWN: 6
FEASIBLE: 0
```

The sample-500 diagnostic is therefore not fully closed; the stubborn tail is
real and remains concentrated under:

```text
base65535_sub1519 chunk 7
base65535_sub1533 chunk 3
base65535_sub1535 chunks 3,5,7
base98303_sub1535 chunks 3,5,7
```

Worst-bucket A/B collection over `[61575,66575)`:

```text
baseline 60s degree-order: 4320 INFEASIBLE, 680 UNKNOWN, 0 FEASIBLE, UNK 13.60%
reorder 60s enrich-order: 4352 INFEASIBLE, 648 UNKNOWN, 0 FEASIBLE, UNK 12.96%
walltime 300s degree-order: 4632 INFEASIBLE, 368 UNKNOWN, 0 FEASIBLE, UNK 7.36%
```

Interpretation:

- Reordering hot pins is only marginal; it is not the main lever.
- A 300s cap helps substantially but still leaves a high hard-pocket rate.
- The hard pocket looks structural, not merely an artifact of variable order or
  too-short 60s slices.

Recommendation:

Do not submit the full 12.5M sweep under the current architecture.  Next useful
move is either a stronger pruning layer for the middle-window hard pocket or a
very small exploratory level-4 tail cleanup only to characterize the six
remaining sample-tail UNKNOWNs.  Treat the broad+refine brute path as expensive
and not yet justified.

## 2026-05-23 level-4 cleanup and pair-clause benchmark

Track 1 level-4 cleanup was emitted from the six remaining level-3 UNKNOWN rows.
Important: the first emit used a too-coarse parent-tag regex and would have
collided output names for subchunks `3`, `5`, and `7`; that job was canceled
immediately.  The corrected emit includes the parent level-3 subchunk in the
tag.

```text
canceled bad emit: job 58377969
correct level-4 job: 58377971
script: submit_tail_sample500_level4_next8_unique.sbatch
output prefix: results/refine_N212_K44_window100k_sample500_tail_level4_unique_*
array: 0-5%6
```

Track 2 pair-clause propagation A/B was launched on the first level-3 residual:

```text
parent: results/refine_N212_K44_window100k_sample500_tail_level3_base65535_sub1535_subchunk3_next8_60.jsonl
parent chunk_id: 0
bad placeholder job canceled: 58377972
correct benchmark job: 58377979
script: bench_pair_clauses_level3_base65535_sub1535_subchunk3.sbatch
control output: results/pair_bench_level3_base65535_sub1535_subchunk3_control_v2.jsonl
treatment output: results/pair_bench_level3_base65535_sub1535_subchunk3_treatment_v2.jsonl
treatment flag: --pair-clauses-window 67,91
```

Monitor:

```bash
squeue -j 58377971,58377979
grep -R '"status": *"FEASIBLE"' \
  ~/erdos_r3/results/refine_N212_K44_window100k_sample500_tail_level4_unique_*_next8_60.jsonl \
  ~/erdos_r3/results/pair_bench_level3_base65535_sub1535_subchunk3_*_v2.jsonl
```

If the pair-clause treatment closes while control stays UNKNOWN, the redundant
propagation layer is worth scaling to a few more residuals.  If treatment equals
control and level-4 still leaves UNKNOWNs, treat the pocket as CP-SAT-resistant
under this formulation.

## 2026-05-23 cap-recalibration diagnostics

The pair-clause benchmark was not a useful scaling lever: both control and
treatment closed the selected residual, with control slightly faster.

```text
control: INFEASIBLE in 67.843s
treatment (--pair-clauses-window 67,91): INFEASIBLE in 71.75s
```

The better hypothesis is that the 60s cap is too short for some hard tails.  To
test that before designing new math, three bounded jobs were submitted:

```text
tail600 level-4 control: job 58377988
  script: submit_tail_level4_cap600.sbatch
  output prefix: results/refine_N212_K44_window100k_sample500_tail_level4_control600_*
  tasks: 6, cap: 600s

recap120 sample100: job 58377989
  script: submit_recap120_sample100.sbatch
  chunk list: results/N212_K44_window100k_recap_sample100.json
  shard dir: results/broad24_window_recap120_sample100
  tasks: 100, cap: 120s

recap300 sample100: job 58377990
  script: submit_recap300_sample100.sbatch
  chunk list: results/N212_K44_window100k_recap_sample100.json
  shard dir: results/broad24_window_recap300_sample100
  tasks: 100, cap: 300s
```

Sample100 was drawn from the 6,071 UNKNOWN chunks in
`results/N212_K44_broad24_window_11575_111574.jsonl` with random seed `5230`.
The local/remote `r3_slurm_emit.py` now supports phase-2 `--chunk-list` by
running one sampled broad chunk per SLURM task via `--only-chunk-id`; `r3_collect.py`
also supports `--chunk-list` for clean sampled reports.

Monitor:

```bash
squeue -j 58377988,58377989,58377990
grep -R '"status": *"FEASIBLE"' \
  ~/erdos_r3/results/refine_N212_K44_window100k_sample500_tail_level4_control600_*_next8_600.jsonl \
  ~/erdos_r3/results/broad24_window_recap120_sample100/*.jsonl \
  ~/erdos_r3/results/broad24_window_recap300_sample100/*.jsonl
```

After recap jobs drain, collect:

```bash
PY=/work/pi_ergezerm_wit_edu/ergezerm_wit_edu-conda/envs/soft/bin/python
$PY r3_collect.py \
  --shard-dir results/broad24_window_recap120_sample100 \
  --chunk-list results/N212_K44_window100k_recap_sample100.json \
  --out results/N212_K44_broad24_recap120_sample100.jsonl
$PY r3_collect.py \
  --shard-dir results/broad24_window_recap300_sample100 \
  --chunk-list results/N212_K44_window100k_recap_sample100.json \
  --out results/N212_K44_broad24_recap300_sample100.jsonl
```

Decision rule: if all six tail cases close under 600s and recap120 has
`UNKNOWN <= 1%`, treat the 60s cap as the main bug.  If tail600 still has
UNKNOWNs, pause broad compute and pivot to stronger bounds/custom B&B.

## 2026-05-23 cap-recalibration results

Jobs `58377988`, `58377989`, and `58377990` all drained.  No FEASIBLE rows
appeared.

Tail600 control over the six level-4 residuals:

```text
INFEASIBLE: 6
UNKNOWN: 0
FEASIBLE: 0
seconds by case: 63.06, 127.26, 599.74, 65.92, 132.85, 291.33
```

This means the six sample-tail cases are slow but closable with a longer cap.
One case essentially used the full 600s limit, so the tail is still expensive.

Broad recap sample from the 6,071 UNKNOWNs in the 100k window-bound batch:

```text
recap120 sample100: 31 INFEASIBLE, 69 UNKNOWN, 0 FEASIBLE
recap300 sample100: 55 INFEASIBLE, 45 UNKNOWN, 0 FEASIBLE
```

The recap sample is conditional on chunks already being UNKNOWN at 60s, so these
are closure rates among prior failures, not full-broad UNKNOWN rates.  Still,
the result is negative for the "just raise the cap" hypothesis: 120s closes only
31% of sampled UNKNOWNs, and 300s closes 55%, leaving a large residual tail.

Collected reports:

```text
results/N212_K44_broad24_recap120_sample100.jsonl
results/N212_K44_broad24_recap300_sample100.jsonl
```

Interpretation:

- 60s is too short for some refinement tails.
- But broad-pass UNKNOWNs do not collapse under 120s or 300s.
- Current CP-SAT architecture remains too expensive for a full 12.5M sweep.

Recommendation:

Do not submit broader compute under the current setup.  The next serious move
should be a stronger bounding method for the hard pocket: LP/ILP cuts, custom
branch-and-bound with strong node upper bounds, or a different mathematical
attack.  A small methodology writeup is also plausible: window bounds + split
diagnostics expose a reproducible structural hard pocket around the middle
witness pins.
