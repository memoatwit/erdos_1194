# Overnight Plan: Erdős r_3 Frontier

Date: May 18, 2026

## Current State

We pivoted from the Nielsen covering-system reproduction to the exact
3-term-arithmetic-progression-free problem:

```text
r_3(N) = max {|A| : A subset {1,...,N}, A has no 3-term AP}.
```

The local verifier and exact reference tools are in place:

- `r3_verify.py`: independent witness verifier.
- `r3_brute.py`: exact DFS, validated against OEIS for small N.
- `r3_milp.py`: exact SciPy/HiGHS MILP model.
- `r3_cpsat.py`: OR-Tools CP-SAT model using local deps in `.deps`.

Important correction: the downloaded OEIS A003002 b-file ends at

```text
211 43
```

not `r_3(211)=33`.  Related sequence A065825 gives threshold values through
`a(43)=209`, meaning a 43-point 3-AP-free set first appears in `{1,...,209}`.
The next unknown threshold is `a(44)`.

## Honest Solver Status

The naive exact models are valid but not yet frontier-grade.

Validated:

```text
MILP:
  N=28 matched OEIS.
  N=40..50 matched OEIS, but N=50 took about 24s.

CP-SAT:
  N=40..61 matched OEIS.
  N=50 optimized correctly in about 10-13s.
  N=62 optimization found a size-19 witness but did not prove optimal in 60s.
  N=62 decision "is there a size-20 set?" did not prove infeasible in 120s.
```

So the next work should not be "run N=212 with the naive model all night."
That would almost certainly produce an inconclusive timeout.

## Implementation Status

The overnight tooling has been implemented:

- `r3_cpsat.py` now supports `--fix-in`, `--fix-out`, `--hint`, and
  `--save-full`.
- `r3_random_greedy.py` found and saved a verified 43-point witness for
  `N=212` at `results/N212_K43_witness.json`.
- `r3_split_cpsat.py` supports resumable JSONL chunking by endpoint pairs and
  by high-incidence variables. It now also supports global `--fix-in` /
  `--fix-out`, AP-pruned degree-variable chunk generation, and CP-SAT branching
  controls.
- `r3_bb.py` is an experimental exact branch-and-bound fallback using dynamic
  AP pruning plus a compatibility-coloring upper bound.

Diagnostics from the first proof attempts:

```text
N=62, K=20 monolithic calibration:
  UNKNOWN after 300s.

N=62, K=20 endpoint split smoke:
  first 5 chunks all INFEASIBLE, hardest 20.6s.

N=212, K=44 endpoint split, pairs=10:
  chunk 0 UNKNOWN after 600s.

N=212, K=44 endpoint split, pairs=12:
  chunk 0 UNKNOWN after 600s.

N=62, K=20 degree-var split smoke:
  mixed UNKNOWN/INFEASIBLE under 10s chunk cap.

N=212, K=44 endpoint-forced degree split:
  Since `r_3(211)=43`, any 44-set in `[1,212]` must contain both endpoints
  `1` and `212`; otherwise it restricts or translates to a 44-set in
  `[1,211]`.  This necessary condition is saved as
  `results/N212_K44_force_endpoints.json`.

  Degree splits with endpoint forcing and AP-prefix pruning still produced
  `UNKNOWN` on the first few chunks at a 60s cap for split counts 22, 28, and
  32.  This suggests the current CP-SAT proof architecture is still
  underpowered, but a 600s/chunk overnight probe remains useful for honest
  hard-chunk data.
```

Conclusion: endpoint-pair splitting alone is not enough.  The next long run
should use the high-incidence variable strategy, and future work may need a
more mathematical branching heuristic if the hardest chunks remain UNKNOWN.

## Win Conditions

Best near-term exact-value win:

```text
Prove r_3(212) = 43.
```

Because `r_3(211)=43`, this only requires proving there is no 44-point
3-AP-free subset of `{1,...,212}`.  A 43-point lower bound is inherited from
`N=211`.

Alternative lower-bound win:

```text
Find a 44-point 3-AP-free set in {1,...,N}.
```

This would improve/extend threshold knowledge for A065825, but it would not by
itself give an exact A003002 value unless we also prove no 45-point set at that
N.

## Tonight's Plan

### Phase 1: Make CP-SAT Search More Useful

Add three practical features to `r3_cpsat.py`:

1. `--fix-in PATH` / `--fix-out PATH`: fix selected variables to 1 or 0.
2. `--hint PATH`: give CP-SAT a known AP-free set as a solution hint.
3. `--save-full PATH`: write full solver output even for inconclusive runs.

These are small engineering tasks and make the rest of the night reproducible.

### Phase 2: Build Lower-Bound Search For 44-Sets

Create `r3_random_greedy.py` or similar:

1. randomized greedy construction with restarts,
2. local repair/swap search,
3. target size `K=44`,
4. sweep `N=212..260`,
5. save every verified 44-set found.

This is likely faster than asking CP-SAT to find a witness cold.  If it finds a
44-set at small N, that becomes a strong hint for CP-SAT and a useful result
even before exactness.

Suggested command shape:

```bash
python3 erdos_r3/r3_random_greedy.py \
  --N-start 212 --N-end 260 --target 44 \
  --restarts 20000 \
  --output erdos_r3/results/greedy_44_sweep.json
```

### Phase 3: Split The Upper-Bound Proof For N=212

Create a split runner for the decision problem:

```text
Does there exist a 44-point 3-AP-free subset of [1,212]?
```

Do not run one monolithic CP-SAT job.  Split by a small prefix or by reflected
endpoint pairs.

Recommended first split:

1. Use reflection symmetry.
2. Branch on the first 16 reflected pairs:
   `(1,212), (2,211), ..., (16,197)`.
3. Enumerate only assignments whose selected prefix is itself AP-compatible.
4. For each chunk, run CP-SAT with fixed variables and `sum == 44`.
5. Save each chunk as `OPTIMAL/INFEASIBLE`, `FEASIBLE`, or `UNKNOWN`.

The goal is not necessarily to finish all chunks tonight.  The goal is to find
whether chunking makes infeasibility proofs tractable.

Suggested output:

```text
erdos_r3/results/N212_K44_split_prefix16.jsonl
```

Each line should record:

```json
{
  "chunk_id": 17,
  "fixed_in": [1, 4, ...],
  "fixed_out": [212, 209, ...],
  "status": "INFEASIBLE",
  "seconds": 93.2,
  "branches": 123456,
  "conflicts": 7890
}
```

### Phase 4: Overnight Queue

After implementing the split runner:

1. Run a short calibration on known hard-ish values:

```bash
python3 erdos_r3/r3_cpsat.py 62 --decision-size 20 --time-limit 300 --workers 8
```

2. If the split runner exists, start the real proof attempt:

```bash
python3 erdos_r3/r3_split_cpsat.py \
  --N 212 --K 44 \
  --pairs 16 \
  --chunk-time-limit 600 \
  --workers-per-chunk 8 \
  --output erdos_r3/results/N212_K44_split_prefix16.jsonl
```

3. In parallel only if the machine has enough headroom, run lower-bound search:

```bash
python3 erdos_r3/r3_random_greedy.py \
  --N-start 212 --N-end 260 --target 44 \
  --restarts 20000 \
  --output erdos_r3/results/greedy_44_sweep.json
```

## Morning Evaluation

Good outcomes:

- `N=212, K=44` split proof finishes all chunks infeasible:
  conclude `r_3(212)=43`.
- Greedy/local search finds a 44-set:
  verify it and use it as a CP-SAT hint; update target to exactness around the
  first found N.
- Split proof does not finish but many chunks close quickly:
  increase split depth or distribute chunks.

Bad but useful outcome:

- Most chunks are `UNKNOWN` after 10 minutes each.
  This means CP-SAT needs a stronger custom branch-and-bound or a different
  exact method before touching N=212 seriously.

## Recommendation

Tonight should prioritize infrastructure that creates interpretable evidence:

1. implement CP-SAT fixed-variable/hint/save support,
2. implement randomized lower-bound search,
3. implement split CP-SAT runner,
4. start the `N=212, K=44` split proof only after the split runner is logging
   cleanly.

Do not spend the whole night on one opaque `r3_cpsat.py 212 --decision-size 44`
run.
