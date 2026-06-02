# Writeup outline: A CP-SAT-based attack on r_3(212), with a characterization of a structural hard pocket

This is a working outline for a methodology preprint documenting the
`r_3(212)` upper-bound campaign. The HiGHS prototype outcome is now nuanced:
it closed `0 / 45` of the 300s-resistant hard survivors at a one-hour cap,
but a five-chunk eight-hour pilot closed `3 / 5` while leaving `2 / 5` with
dual bound still pinned at `0.0`.

## Working title (3 candidates)

1. *A reproducible CP-SAT framework for r_3(N) upper-bound search, with empirical evidence at N=212*
2. *Witness-split + window-cardinality refinement for r_3(N): architecture, empirical results, and a structural hard pocket*
3. *Toward r_3(212) ≤ 43: a million-subproblem CP-SAT search and the structural pocket that resists it*

Title 2 best balances accuracy and reach.

## One-paragraph abstract draft

> We describe a reproducible CP-SAT-based search architecture for upper bounds
> on `r_3(N)`, the size of the largest 3-AP-free subset of `{1, ..., N}`. The
> architecture combines a verified lower-bound witness, endpoint forcing,
> depth-`d` witness-variable splitting, OEIS A003002 window-cardinality
> pruning, and recursive refinement. Applied to `N = 212, K = 44`, it processed
> millions of subproblems on a SLURM cluster and found no feasible 44-set,
> strongly supporting the OEIS-conjectured value `r_3(212) = 43` but not
> proving it. The main outcome is a structural hard pocket: a 300-second recap
> left `45` resistant chunks; one-hour HiGHS MIP closed `0 / 45`, while an
> eight-hour five-chunk pilot closed `3 / 5` and left `2 / 5` with dual bound
> still `0.0`. We characterize this pocket, release tiered benchmark instances,
> and frame the remaining unit-gap problem as a target for stronger
> additive-combinatorial bounds, custom branch-and-bound, SAT proof logging, or
> formal proof-search workflows.

## Section outline

### 1. Introduction & background (~1 page)

- Statement of `r_3(N)` and the Erdős conjecture line of work.
- OEIS A003002 frontier and Cariboni's b-file up to `n = 211`.
- The standard formulation: `x_i ∈ {0, 1}`, `x_a + x_b + x_c ≤ 2` for
  every 3-AP triple.  CP-SAT applicability.
- Our concrete target: prove `r_3(212) ≤ 43`, given the verified 43-point
  witness `A_43 ⊂ [1, 212]`.
- Conditional pruning input: `r_3(211) = 43` from A003002 implies any
  44-set in `[1, 212]` must contain both endpoints `1` and `212`.

### 2. Architecture (~2 pages)

#### 2.1 Decision-form CP-SAT model
- Hard equality `sum x_i = K` instead of `≥ K` (tighter).
- 3-AP linear constraints.
- Reflection symmetry break (lex constraint).
- Branch strategy: `degree` ordering, `min` value, `fixed_search`.

#### 2.2 Witness-variable splitting
- Pick the lower-bound witness `A_43`; rank its elements by AP-incidence
  degree.  Top-24 form the broad split.
- For each of the `2^24` assignments of the 24 witness pins to {in, out},
  apply AP-prefix pruning; surviving chunks are the broad workload.

#### 2.3 Window-cardinality pruning
- For each window `[a, a+L-1]` and each `L` with `r_3(L) < L`, add
  `sum x_i ≤ r_3(L)` derived from OEIS A003002.
- For `N=212, K=44`: ~22,154 window constraints generated.

#### 2.4 Recursive refinement
- Any chunk timing out is refined: pick the next-degree witness vars and
  split deeper.  Standard depths used: broad `+ 16` (depth 40), residuals
  `+ 8` (depth 48 then 56).

#### 2.5 Engineering: SLURM emitter, shard collector, tail emitter
- `r3_slurm_emit.py`, `r3_collect.py`, `r3_tail_emit.py`, `r3_proof_manager.py`.
- Atomic shard rename pattern.  QOS-aware tranching.
- Reproducible from this repo with the `unity_handoff.sh` script.

### 3. Empirical campaign (~2 pages)

#### 3.1 Chunk-count breakdown
- Verified lower bound: 43-point witness (see `results/N212_K43_witness.json`).
- Broad pass at depth 24, 60s wall, window-bounds:
  - Calibration `[575, 1574]`: 1,000 chunks → 799 INFEASIBLE, 201 UNKNOWN.
  - Bounded `[1575, 11575)`: 10,000 → 6,967 INF, 3,033 UNK at 60s; with
    window-bounds 9,835 INF, 165 UNK.
  - Expansion `[11575, 111575)`: 100,000 → 93,929 INF, 6,071 UNK.
- Recursive refinement: 100/100 sample-100 random UNKs closed; 500/500
  stratified sample with 10 residuals; sample-500 tail8 closed except
  6 residuals at depth 56; the 6 residuals at 600s wall all closed at
  depth 56 (max 599.74s).

#### 3.2 The window-cardinality A/B
- A/B on `[575, 675)`: 27% UNK at 60s without window-bounds → 0% with.
- 10k batch `[1575, 11575)`: 30.33% UNK without → 1.65% with.
- 100k batch `[11575, 111575)`: 6.07% UNK with window-bounds.
- Interpretation: window-bounds are essential but the UNK rate grows with
  chunk index, indicating non-uniform hardness.

#### 3.3 Levers tested and outcomes
| Lever | Outcome on hard bucket `[61575, 66575)` |
|---|---|
| Baseline 60s window-bounds | 13.60% UNK |
| Split-vars reorder (enrichment first) | 12.96% UNK (noise-level) |
| Walltime extension 60s → 300s | 7.36% UNK (saturating curve) |
| Targeted pair-AND propagators on `[67,91]` | No measurable change vs control on a sampled residual |
| Recursive deepening to depth 56 + 600s | 6/6 close, max 599.74s |
| 100k window-batch recap at 120s/300s | Surviving UNK still 45/100 at 300s |

#### 3.4 Zero FEASIBLE across the campaign
- Total CP-SAT subproblems solved (broad + refinement levels): millions,
  with exact retained-log counts tabulated in §3.
- Number returning FEASIBLE: 0.
- This is moral evidence for `r_3(212) ≤ 43` but does not constitute a proof.

### 4. The structural hard pocket (~1.5 pages)

#### 4.1 Empirical signature on the population
- The 6,071-UNK 100k population has a clean pin-OUT enrichment signal:
  values `{68, 70, 75, 76, 91}` OUT each correlate with ~9.7% UNK vs
  ~2.5% IN.  These are all in the dense middle `[67, 91]` region of the
  43-witness.
- Hot bucket `[61575, 66575)` has UNK rate 13.60%, ~2.2× baseline.

#### 4.2 The 300s-resistant tail does not collapse
- 45 of 100 sampled UNKs survived a recap at 300s broad wall.
- Top single-pin enrichment retains the `{68, 70, 75, 76, 91}` signal
  but with weaker effect sizes.
- Top pair pattern: `[91=OUT, 48=OUT]` at 66.67% UNK coverage,
  log-odds +1.226.  No high-coverage triple cleanly separates UNK from
  INF on the survivor set.
- Hamming clustering of survivor `fixed_in` sets shows multiple small
  clusters, not a single dominant niche.
- Interpretation: the surviving hard subproblems share moderate pin-OUT
  structure but spread across many distinct sub-pockets.  No clean
  targetable signature.

#### 4.3 What we tried and why none worked
- Pair-AND Tseitin propagators on `[67, 91]`: control 67.84s vs treatment
  71.75s on the same residual.  Mathematically redundant; empirically
  not faster.
- Order-within-broad-24 reorder: no effect (within-prefix order does not
  change the surviving chunk set, only iteration order under AP-pruning).
- Walltime extension at the broad layer: saturating curve.  Doubling
  wall closes ~31% of UNKs; further doubling closes ~24% more, then
  plateaus.

#### 4.4 Conjecture about the pocket
- The hard pocket appears to correspond to a region of the depth-24
  assignment lattice where the LP relaxation gap is small (so window
  bounds barely cut) AND the search tree's natural branching cannot
  reach a contradiction within a few hundred milliseconds of CP-SAT
  inference per node.
- The pocket is *not* a single combinatorial structure; it is plausibly
  a low-dimensional manifold in the assignment lattice.

### 5. Open problem (~0.5 page)

Formulate cleanly:

> Given `N = 212, K = 44`, the explicit 43-witness, the list of forced
> `{1, 212}`, and the window-cardinality bounds from OEIS A003002, find
> either a 44-element 3-AP-free subset of `[1, 212]` or a proof that
> none exists, in a way that closes all 6,071 UNKNOWN chunks of the
> 100k window-bound batch (or all `12,582,912` AP-pruned depth-24
> chunks of the full sweep).

State that:
- Our CP-SAT pipeline is fully open-source and reproducible.
- The 6,071 UNKNOWN chunks and the 45 300s-resistant survivors are
  released as benchmark instances in `results/`.
- A specialist with a stronger MIP/B&B framework could pick up exactly
  this set and either close the proof or push the hard frontier further.

### 6. Discussion (~0.5 page)

- Reusability: the architecture works for any `r_3(N')` upper-bound
  attack given a verified `(N'-1)` lower-bound witness and an OEIS
  b-file prefix.  We expect it to be useful for `N \in \{213, ..., 220\}`
  with minor tuning.
- Limitations: hard pockets at larger `N` may be much worse and shift the
  break-even point of refinement vs broad walltime.
- Future work: hand off the hard-pocket benchmark to specialists with
  custom MIP/B&B code; explore SDP/Fourier relaxations as alternative
  upper-bound sources at the broad layer.

### Appendices

- A. Verification of the 43-witness (`r3_verify.py` and OEIS cross-check).
- B. Full configuration of CP-SAT used (workers, branching, seeds).
- C. SLURM scripts and job IDs of the campaign.
- D. Per-bucket UNK rate table for the 100k batch.
- E. The 6,071 UNK chunk IDs (released as a JSONL file).

## Figures to produce

1. **UNK rate vs chunk index** for the three batches (calibration, 10k,
   100k).  Shows growth with N, motivates the "uniform hardness fails"
   observation.
2. **Hot-bucket UNK rate vs wall cap** (60s, 120s, 300s, 600s) — the
   saturating curve.
3. **Per-bucket UNK rate** (5k-wide bins across `[11575, 111575)`).
4. **Pin-OUT enrichment plot** (log-odds for each of the 24 broad split
   variables, UNK vs INF).
5. **Refinement depth tree** showing original UNK → depth-16 sample-500
   → depth-8 tails → depth-8 level-3 → depth-8 level-4.
6. **Hamming cluster diagram** for the 45 300s-resistant survivors.

## Open decisions

- Venue: arXiv preprint vs proceedings (FPSAC / CPM / SAT).  Arxiv first
  is safe.
- Co-authorship and acknowledgments.
- HiGHS prototype outcome is known: `0 / 45` closed, so the negative-result
  framing is stronger.

## HiGHS prototype outcome

HiGHS closed `0 / 45` of the 300s-resistant survivor chunks in one-hour
per-chunk runs. This supports the current Section 4 framing: the hard pocket
is not merely a CP-SAT propagation artifact, and generic LP-relaxation-based
MIP machinery does not immediately close it either.
