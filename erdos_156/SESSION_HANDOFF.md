# Phase 9 session handoff (#156)

## Current state

- Exact \(m(N)\) is known for \(N = 5, 10, 15, \ldots, 125\).
- Latest exact value: \(m(125)=8\), certified by a complete k=7 split and a
  size-8 witness.
- Heuristic upper-bound extension: a parametrized shifted size-8 template
  gives maximal Sidon sets for every \(N=113,\ldots,144\). Exact lower
  bounds were not certified beyond the existing table.
- Follow-up shifted templates give construction-based witnesses through
  \(N=187\): size 9 covers \(145,\ldots,161\), and size 10 covers
  \(150,\ldots,187\).
- Tools available:
  - `solve_156.py` — Python verifier / sweep / hunt / MILP prototype.
  - `search156.cpp` / `search156` — C++ exact DFS with coverage-order
    tie-break, leaf-only maximality, and reflection symmetry check.
  - `cpsat_156.py` — ortools CP-SAT model for fixed \((N,k)\) maximality.
    Too large to be useful at \(N\ge 50\): blocker encoding expands to
    \(O(N^3)\) auxiliary Booleans.
  - `search156_v2.cpp` / `search156_v2` — tried per-candidate coverage
    pruning by recomputing addability. Correct but slower than v1.
  - `search156_v3.cpp` / `search156_v3` — **current best exact checker**.
    Maintains the addable/unblocked set incrementally and uses cheap
    coverage pruning at every node.
  - `search156_v4.cpp` / `search156_v4` — v3 plus first-element range
    splitting. This resolved the hard \(k=7\) infeasibility certificates at
    \(N=105,110,115,120,125\).
  - `run_split_exact.py` — resumable wrapper around `search156_v4`; used to
    certify \(N=125,k=7\) over all canonical first elements.
  - `repair_125_k8.py` — targeted size-8 witness search using seeded
    one-swap repair and randomized coverage-first rebuilds. This found the
    first \(N=125,k=8\) witness after v3 and random hunt missed it.
  - `mine_structure.py` — structural mining of witnesses as
    \(A\pm\Delta(A)\) covers.
  - `local_repair_156.py` — exhaustive radius-swap search around a fixed
    near-miss.
  - `parametrize_template.py` — computes the relative blocker set \(W(B)\),
    long consecutive blocker intervals, and feasible shifts for a template.
  - `extend_template_chain.py` — reproducible greedy one-point extension
    search for shifted-template chains.
  - `beam_template_search.py` — beam search that keeps many shifted templates
    per size and optimizes blocker-interval length divided by \(k^3\).
  - `search_template_architectures.py` — generates diversified dense-core
    plus-anchor seeds, ranks them, and extends the best seeds with beam search.
  - `local_optimize_template.py` — fixed-size one-swap plus annealing optimizer
    for shifted templates.
  - `analyze_anchor_cover.py` — decomposes a template's blocker interval by
    core-core, core-anchor, anchor-anchor, midpoint, and in-template sources.
  - `overnight_plan_anchor_layers.md` — next overnight plan focused on
    anchor-layer search and formula extraction.
  - `overnight_run_status_anchor_layers.md` — status note for the current
    overnight run.

## Exact table

| \(N\) | \(m(N)\) | witness |
|----:|------:|---------|
| 5 | 3 | `[1, 2, 4]` |
| 10 | 3 | `[2, 5, 6]` |
| 15 | 4 | `[1, 2, 4, 12]` |
| 20 | 4 | `[1, 8, 12, 13]` |
| 25 | 5 | `[1, 2, 4, 10, 23]` |
| 30 | 5 | `[1, 4, 11, 15, 17]` |
| 35 | 5 | `[1, 12, 13, 18, 22]` |
| 40 | 5 | `[3, 16, 17, 24, 26]` |
| 45 | 6 | `[1, 2, 4, 19, 23, 31]` |
| 50 | 6 | `[1, 2, 15, 22, 24, 27]` |
| 55 | 6 | `[1, 8, 22, 25, 31, 44]` |
| 60 | 6 | `[1, 18, 21, 30, 36, 40]` |
| 65 | 6 | `[9, 25, 26, 32, 40, 45]` |
| 70 | 7 | `[8, 23, 27, 29, 40, 47, 52]` |
| 75 | 7 | `[15, 24, 25, 39, 42, 47, 58]` |
| 80 | 7 | `[25, 34, 36, 40, 48, 64, 65]` |
| 85 | 7 | `[23, 33, 44, 45, 58, 61, 63]` |
| 90 | 7 | `[13, 29, 36, 37, 51, 57, 62]` |
| 95 | 7 | `[3, 37, 39, 43, 51, 54, 78]` |
| 100 | 7 | `[8, 42, 44, 48, 56, 59, 83]` |
| 105 | 8 | `[1, 3, 13, 34, 47, 50, 58, 88]` |
| 110 | 8 | `[11, 46, 50, 53, 59, 75, 83, 93]` |
| 115 | 8 | `[1, 3, 43, 47, 53, 61, 66, 96]` |
| 120 | 8 | `[43, 44, 56, 60, 75, 78, 86, 115]` |
| 125 | 8 | `[5, 42, 45, 49, 64, 76, 77, 87]` |

See `results/exact_156_summary.md` and per-\(N\) JSON files for logs.

## New structural/upper-bound data

Overnight structural mining found a reusable size-8 shifted template:

```text
B = [0, 40, 60, 61, 63, 67, 96, 112]
gaps(B) = [40, 20, 1, 2, 4, 29, 16]
```

The parametrized blocker set

\[
W(B)=B\cup(B+\Delta(B))\cup(B-\Delta(B))\cup\text{integer midpoints}(B)
\]

contains the full interval \([-7,136]\).  Therefore a shift \(A=s+B\) is
certified whenever

\[
\max(1,N-136)\le s\le \min(8,N-112).
\]

This gives maximal Sidon sets for every \(N=113,\ldots,144\). The same
template cannot cover \(N=145\): for any valid shift \(s\le8\), the point
\(s+137\) lies in \([1,145]\) and hits the relative hole \(137\notin W(B)\);
for any valid shift \(s\ge9\), the point \(s-8\) lies in \([1,145]\) and hits
the relative hole \(-8\notin W(B)\).

The next shifted templates now checked are:

```text
B9  = [0, 40, 60, 61, 63, 67, 96, 112, 144]
W(B9)  contains [-12,148], covering N=145..161.

B10 = [0, 40, 60, 61, 63, 67, 96, 112, 144, 149]
W(B10) contains [-29,157], covering N=150..187.
```

Thus construction-based witnesses now cover every \(N=113,\ldots,187\).  The
efficiency is decreasing, however: the interval lengths are \(144,161,187\)
for sizes \(8,9,10\), with ratios to \(k^3\) about \(0.281,0.221,0.187\).
This is finite progress, not yet an asymptotic family.

A reproducible greedy continuation now reaches size 20:

```text
k=20 template =
[0, 40, 60, 61, 63, 67, 96, 112, 144, 149,
 158, 183, 213, 286, 312, 340, 378, 425, 539, 550]
W(B20) contains [-207,580], covering N=551..788.
```

This verifies many more finite witnesses, but the endpoint ratio drops to
\(788/20^3\approx0.0985\).  This strongly suggests that greedy endpoint
extension is not the asymptotic construction.  The next computational move is
a beam/local search optimizing interval length divided by \(k^3\), not just
the next endpoint.

That beam search has now been run.  The best overlap-preserving size-20 beam
template is

```text
[0, 40, 60, 61, 63, 67, 96, 112, 137, 142,
 151, 201, 259, 267, 301, 395, 482, 510, 608, 700]
```

with \(W(B)\supset[-201,711]\), so it covers \(N=701,\ldots,913\).  Its saved
ancestry has overlapping covered ranges whose union is \(N=113,\ldots,913\).
The endpoint ratio is \(913/20^3\approx0.1141\), better than greedy but still
well below the size-8 ratio.  A no-overlap beam run to size 16 did not improve
density, and a one-swap local pass around the best size-20 template found no
improvement up to replacement value 1000.

Interpretation: beam search improves finite witnesses but does not rescue this
specific architecture as an asymptotic construction.  Next best move is to
search for different template architectures that keep interval length/\(k^3\)
from decaying.

The first architecture-diversified search found a better seed:

```text
B8_alt = [0, 20, 35, 38, 39, 44, 46, 95].
```

Extending this seed to size 20 gives

```text
B20_alt =
[0, 20, 35, 38, 39, 44, 46, 95, 111, 132,
 142, 175, 267, 289, 301, 341, 410, 489, 594, 617]
```

with \(W(B20\_alt)\supset[-273,648]\), covering \(N=618,\ldots,922\).  The
path ancestry has overlapping ranges whose union is \(N=96,\ldots,922\).  This
slightly improves the size-20 endpoint ratio to \(922/20^3=0.11525\).  A small
core-5 seed pass rediscovered the same seed as its best extension.

Interpretation after option 1+2: seed diversification matters and improves the
finite witness range, but the improvement is incremental.  The downward
normalized trend remains.

Option 3/4 local optimization was then run around `B20_alt`.  One replacement,
`111 -> 681`, improved the size-20 template to

```text
B20_local =
[0, 20, 35, 38, 39, 44, 46, 95, 132, 142,
 175, 267, 289, 301, 341, 410, 489, 594, 617, 681]
```

with \(W(B20\_local)\supset[-273,693]\), covering \(N=682,\ldots,967\).  The
endpoint ratio is now \(967/20^3=0.120875\).  A second pass with exhaustive
one-swap search up to replacement value 1400 and annealing found no further
improvement.  Combining this template with the architecture beam path gives
construction witnesses for every \(N=96,\ldots,967\).

Formula-extraction readout: the template has a 7-mark dense core
`[0,20,35,38,39,44,46]` with gaps `[20,15,3,1,5,2]`, then sparse anchor
layers.  The full template creates all differences `1..12`; the right endpoint
of the blocker interval is `681+12=693`, while the adjacent holes are `-274`
and `694`.  This still looks like compact small-difference core plus translated
anchor coverage, not yet a stable asymptotic formula.

Anchor-cover model check:

- Starting from only the 7-mark core `[0,20,35,38,39,44,46]`, the overlap
  beam search builds a size-20 fixed-core anchor chain with covered union
  \(N=47,\ldots,935\).  This confirms the core can support a long anchor-cover
  chain, though it is below the locally optimized \(N=967\) endpoint.
- Source decomposition for `B20_local` over `[-273,693]`:
  - core-anchor difference events: 2637
  - anchor-anchor difference events: 2565
  - core-core difference events: 829
  - midpoint events: 91
  - in-template events: 20
- Point coverage categories: core-anchor differences hit 919/967 relative
  points, anchor-anchor differences hit 859/967, and core-core differences hit
  495/967.

Interpretation for formula extraction: a formula based only on translating a
fixed core-difference set by anchors is probably too weak.  The best templates
use anchor-anchor differences almost as heavily as mixed core-anchor
differences.  A scalable construction would need an anchor-layer design whose
pairwise differences deliberately fill the gaps between mixed core translates.

Next overnight plan:

- See `overnight_plan_anchor_layers.md`.
- Priorities: fixed-core beam to \(k=24/28\), deeper local optimization of
  `B20_local`, broader core-4/core-5 architecture seed searches, then source
  decomposition of any new best template.
- Success criteria: endpoint ratio stays at least `0.120` beyond size 20, any
  new size-20 endpoint beats `967`, or a repeated anchor-layer pattern emerges.

Current overnight run status:

- See `overnight_run_status_anchor_layers.md`.
- Completed fixed-core beams:
  - k=24, union \(N=47,\ldots,1453\), final ratio \(1453/24^3=0.1051\).
  - k=28, union \(N=47,\ldots,2122\), final ratio \(2122/28^3=0.0967\).
- Completed deep local search from `B20_local`: no improvement over
  \(967/20^3=0.120875\).
- Completed broad core-4 extension/local optimization:
  - k=20 improved endpoint to \(968/20^3=0.121\).
  - k=24 improved endpoint to \(1490/24^3\approx0.10778\).

Morning update: the broad core-4 search completed.  Best seed:

```text
[0, 15, 35, 38, 39, 44, 46, 95]
```

Its best path has covered union \(N=96,\ldots,758\), with final row
\(k=18\), covered \(N=511,\ldots,758\), and endpoint ratio
\(758/18^3\approx0.12997\).  Representative witnesses along the path passed
the original verifier.  Next recommended action: extend this seed to k=20 and
k=24 before running more broad seed searches.

May 17 continuation: that extension/local-optimization step has now been run.
Extending the broad seed to k=20 gave a beam path with covered union
\(N=96,\ldots,934\).  Because the final size-20 row was close to the previous
record, local optimization found a one-swap improvement `519 -> 594`:

```text
B20_new =
[0, 15, 35, 38, 39, 44, 46, 95, 114, 136,
 157, 202, 238, 288, 346, 373, 413, 507, 594, 647]
```

For this template \(W(B)\) contains `[-225,742]`, so it covers
\(N=648,\ldots,968\).  The endpoint ratio is
\(968/20^3=0.121\), a small improvement over the previous
`B20_local` endpoint \(967\).  A second local pass found no further
improvement.

Anchor-cover decomposition for `B20_new` was also run.  Over `[-225,742]`,
source event counts are:

```text
core-anchor:   2789
anchor-anchor: 2664
core-core:      840
midpoint:        91
in-template:     20
```

This reinforces the previous structural conclusion: anchor-anchor differences
are nearly as important as core-anchor translates.

The same broad seed was then extended to k=24.  The beam alone covered union
\(N=96,\ldots,1442\).  Two local passes improved the best size-24 endpoint to
1490:

```text
B24_new =
[0, 15, 35, 38, 39, 44, 95, 105, 163, 180, 196, 283,
 296, 310, 404, 478, 519, 694, 792, 845, 864, 1019, 1030, 1051]
```

Here \(W(B)\) contains `[-361,1128]`, covering
\(N=1052,\ldots,1490\), with endpoint ratio
\(1490/24^3\approx0.10778\).  Combined with the broad seed beam ancestry, this
extends deterministic shifted-template coverage from \(N=96\) through
\(N=1490\).  Representative start/middle/end shifts for both new templates
passed interval-lemma validation, both templates are Sidon, and
`solve_156.py verify` confirmed the endpoint witnesses at \(N=968\) and
\(N=1490\).

Diagnostic extension to k=32 was also completed for the same broad-seed/local
architecture:

```text
B32_new =
[0, 15, 35, 38, 39, 44, 95, 105, 163, 180, 196, 283,
 296, 310, 404, 478, 519, 694, 792, 864, 1019, 1030,
 1051, 1153, 1183, 1352, 1438, 1483, 1909, 1928, 1956, 2068]
```

Here \(W(B)\) contains `[-766,2145]`, covering
\(N=2069,\ldots,2912\).  The endpoint ratio is
\(2912/32^3=0.0888671875\), and \(2912\log(32)^2/32^3\approx1.067\).  This
supports the empirical reading that the broad-seed/local architecture is
tracking roughly \(k^3/\log^2 k\), not a constant multiple of \(k^3\).  The
endpoint witness at \(N=2912\) passed `solve_156.py verify`.

Two-scale attempt status: `two_scale_template.py` and `two_scale_plan.md` were
created.  The direct product construction `B=a*S+C` with a fixed nontrivial
core fails because core-core differences repeat across macro tiles, so the
sweep found no valid Sidon/admissible templates.  Singer sets can still be used
as beam seeds, but the completed q=3/q=7 seed checks through k=14 were only
comparable to, not better than, the broad-seed envelope.  The next viable
two-scale redesign should use varied or perturbed cores per macro tile to
avoid repeated small differences.

See `template_parametrization.md`, `parametrize_template.py`, and
`results/template_156_parametrized.json`.

New heuristic upper-bound results:

- \(N=130,k=8\): feasible, e.g.
  `[14, 46, 51, 61, 81, 82, 90, 94]`. The template witness
  `[8, 48, 68, 69, 71, 75, 104, 120]` also works.
- \(N=135,k=8\): feasible with
  `[8, 48, 68, 69, 71, 75, 104, 120]`.
- \(N=140,k=8\): feasible with
  `[4, 44, 64, 65, 67, 71, 100, 116]`.
- \(N=144,k=8\): feasible with
  `[8, 48, 68, 69, 71, 75, 104, 120]`.
- \(N=145,k=8\): not found by two 7200s repair runs; best near-miss
  `[28, 42, 73, 75, 78, 79, 100, 138]` blocks 144/145 and leaves `2`
  addable.
- \(N=145,k=9\): feasible with
  `[1, 32, 52, 56, 65, 73, 95, 100, 101]`.

See `template_parametrization.md`, `overnight_structure_summary.md`,
`structure_mining.md`, `results/structure_156.json`,
`results/template_156_size8_120_144.json`, and
`results/template_156_parametrized.json`, plus
`results/template_156_size9_145_161.json` and
`results/template_156_size10_150_187.json`, and
`results/template_chain_156_greedy.json`, plus
`results/template_beam_156_overlap_k20.json` and
`results/template_beam_156_free_k16.json`, plus
`results/template_architecture_search_156_core4_k16.json`,
`results/template_architecture_search_156_core5_k16.json`, and
`results/template_beam_156_arch_seed_core4_k20.json`, plus
`results/template_local_opt_156_arch20.json` and
`results/template_local_opt_156_arch20_pass2.json`, plus
`results/template_anchor_cover_core7_k20.json`,
`results/template_anchor_cover_core7_free_k16.json`,
`results/anchor_cover_analysis_156.json`, and `anchor_cover_analysis.md`,
plus `results/template_architecture_search_156_core4_broad_k18.json`,
`results/template_beam_156_new_seed_core4_k20.json`,
`results/template_local_opt_156_new_seed_core4_k20.json`,
`results/template_local_opt_156_new_seed_core4_k20_pass2.json`,
`results/template_beam_156_new_seed_core4_k24.json`,
`results/template_local_opt_156_new_seed_core4_k24.json`,
`results/template_local_opt_156_new_seed_core4_k24_pass2.json`,
`results/anchor_cover_analysis_156_new_seed_k20.json`, and
`anchor_cover_analysis_new_seed_k20.md`.

## What v3 changed

v2 showed that coverage pruning is mathematically useful but too expensive
when addability is recomputed for each candidate.

v3 keeps an incremental `Mask unblocked` alongside `A` and `diff_mask`. A bit
is set exactly when that point is still addable to the current partial Sidon
set.

When adding \(x\), v3 clears:

1. \(x\) itself.
2. Points \(x\pm d\) for every already-used or newly-used difference \(d\).
   This matters because old differences become blockers around the new anchor.
3. Points \(a\pm d\) for every old anchor \(a\) and newly-created difference
   \(d=|x-a'|\).
4. New midpoint blockers \((a+x)/2\) for old \(a\in A\).

It also uses a safe future-capacity upper bound for pruning:

\[
1 + 2\binom{j}{2} + 2j(j+1) + j
  = 3j^2 + 2j + 1
\]

for one future insertion from current size \(j\).

## New results from v3

- \(N=95,k=5\): infeasible.
- \(N=95,k=6\): infeasible in 160.86s.
- \(N=95,k=7\): feasible in 240.385s with witness
  `[3, 37, 39, 43, 51, 54, 78]`.
- Therefore \(m(95)=7\).
- \(N=100,k=5\): infeasible.
- \(N=100,k=6\): infeasible in 229.097s.
- \(N=100,k=7\): v3 exact search timed out after 600s, but v4 split search
  found a witness with first element 8:
  `[8, 42, 44, 48, 56, 59, 83]`.
- Therefore \(m(100)=7\).
- \(N=100,k=8\): also feasible, e.g.
  `[4, 26, 37, 38, 43, 57, 64, 73]`.
- \(N=105,k=5\): infeasible in 0.081s.
- \(N=105,k=6\): infeasible in 339.962s.
- \(N=105,k=7\): infeasible by v4 split over all canonical first elements
  \(1,\ldots,53\). Reflection makes this complete because every witness or
  reflected witness has first element at most \(\lfloor(105+1)/2\rfloor=53\).
- \(N=105,k=8\): feasible in 5.860s with witness
  `[1, 3, 13, 34, 47, 50, 58, 88]`.
- Therefore \(m(105)=8\).
- \(N=110,k=5\): infeasible in 0.046s.
- \(N=110,k=6\): infeasible in 532.595s.
- \(N=110,k=7\): infeasible by v4 split over all canonical first elements
  \(1,\ldots,55\). Reflection makes this complete because every witness or
  reflected witness has first element at most \(\lfloor(110+1)/2\rfloor=55\).
- \(N=110,k=8\): feasible via hunt in 5.085s with witness
  `[11, 46, 50, 53, 59, 75, 83, 93]`.
- Therefore \(m(110)=8\).
- \(N=115,k=5\): infeasible in 0.001s.
- \(N=115,k=6\): infeasible in 642.764s.
- \(N=115,k=7\): infeasible by v4 split over all canonical first elements
  \(1,\ldots,58\). Reflection makes this complete because every witness or
  reflected witness has first element at most \(\lfloor(115+1)/2\rfloor=58\).
- \(N=115,k=8\): feasible in 65.273s with witness
  `[1, 3, 43, 47, 53, 61, 66, 96]`.
- Therefore \(m(115)=8\).
- \(N=120,k=6\): infeasible in 699.128s.
- \(N=120,k=7\): infeasible by v4 split over all canonical first elements
  \(1,\ldots,60\). Reflection makes this complete because every witness or
  reflected witness has first element at most \(\lfloor(120+1)/2\rfloor=60\).
- \(N=120,k=8\): feasible via hunt in 262.237s with witness
  `[43, 44, 56, 60, 75, 78, 86, 115]`.
- Therefore \(m(120)=8\).
- \(N=125,k=6\): infeasible in 608.140s.
- \(N=125,k=7\): infeasible by a resumable v4 first-element split over all
  canonical first elements \(1,\ldots,63\). Reflection makes this complete
  because every witness or reflected witness has first element at most
  \(\lfloor(125+1)/2\rfloor=63\). The split searched 2,810,668,688 nodes
  across 63 chunks, with 16,522.156 total reported chunk-seconds. Details:
  `results/exact_156_N125_k7_split.json`.
- \(N=125,k=8\): v3 timed out after 1200.330s with no witness; random hunt
  was also stopped without a certificate.
- \(N=125,k=8\): later feasible via `repair_125_k8.py` with a 15s budget and
  witness `[5, 42, 45, 49, 64, 76, 77, 87]`.
  Independent verifier profile:
  `{in_A: 8, existing_difference: 116, symmetric_collision: 1, addable: 0}`.
  A second verified size-8 witness is `[38, 48, 49, 61, 76, 80, 83, 120]`.
- \(N=125,k=9\): feasible in 0.084s with witness
  `[18, 42, 51, 59, 71, 81, 86, 87, 118]`.
- Therefore \(m(125)=8\).

Before v4 resolved \(N=100,k=7\), the Python `hunt` mode ran 50K trials and
found no witness. Best near-miss:

- `[28, 30, 46, 49, 57, 71, 83]`
- blocks 98 of 100 points
- addable points: `{13, 88}`

A local repair search around that near-miss tried all one-, two-, and
three-element swaps (5,095,160 nearby sets). No witness. Best alternate
near-miss:

- `[30, 36, 47, 55, 57, 71, 83]`
- blocks 98 of 100 points
- addable points: `{7, 86}`

## Useful commands

Build v3:

```bash
clang++ -O3 -std=c++17 erdos_156/search156_v3.cpp -o erdos_156/search156_v3
```

Verify frontier facts:

```bash
erdos_156/search156_v3 95 6 600
erdos_156/search156_v3 95 7 600
erdos_156/search156_v3 100 6 600
erdos_156/search156_v4 100 7 300 8 8
erdos_156/search156_v3 105 5 300
erdos_156/search156_v3 105 6 900
for f in $(seq 1 53); do erdos_156/search156_v4 105 7 450 "$f" "$f"; done
erdos_156/search156_v3 105 8 300
erdos_156/search156_v3 110 5 300
erdos_156/search156_v3 110 6 1200
for f in $(seq 1 55); do erdos_156/search156_v4 110 7 900 "$f" "$f"; done
python3 erdos_156/solve_156.py hunt 110 8 50000
erdos_156/search156_v3 115 5 300
erdos_156/search156_v3 115 6 1800
for f in $(seq 1 58); do erdos_156/search156_v4 115 7 1800 "$f" "$f"; done
erdos_156/search156_v3 115 8 600
erdos_156/search156_v3 120 6 2400
for f in $(seq 1 60); do erdos_156/search156_v4 120 7 2400 "$f" "$f"; done
python3 erdos_156/solve_156.py hunt 120 8 50000
erdos_156/search156_v3 125 6 3000
python3 erdos_156/run_split_exact.py --N 125 --k 7 --workers 8 --output erdos_156/results/exact_156_N125_k7_split.json
erdos_156/search156_v3 125 8 1200
python3 erdos_156/repair_125_k8.py 125 8 15 156
python3 erdos_156/solve_156.py verify 125 5 42 45 49 64 76 77 87
python3 erdos_156/solve_156.py hunt 125 9 50000
python3 erdos_156/solve_156.py hunt 100 7 50000
python3 erdos_156/solve_156.py hunt 100 8 10000
```

Build v4:

```bash
clang++ -O3 -std=c++17 erdos_156/search156_v4.cpp -o erdos_156/search156_v4
```

## Other ideas worth trying

1. **Try to parametrize the shifted template.** The dense core
   `[60, 61, 63, 67]` creates small differences `{1,2,3,4,6,7}`; the anchors
   `0,40,96,112` translate that local coverage. This is the best construction
   clue so far.
2. **Move exact certification to \(N=130\) only if finite exact data matters.**
   Size 8 is feasible there by shifted template; proving exactness would
   require ruling out \(k=7\).
3. **Investigate the \(N=145\) wall.** The shifted size-8 template and repair
   search both stall one point short, while size 9 is immediate.

## Status of #156 attack

- **Not solved.** The Erdős problem \(m(N)=O(N^{1/3})\) is unchanged.
- The empirical ratio \(m(N)/N^{1/3}\) for solved \(N\in[25,125]\) lies in
  roughly \([1.46,1.71]\), consistent with \(N^{1/3}\)-scale behavior but far
  from proof.
- Current exact-search frontier: next multiple is \(N=130\), if continuing
  exact finite certification.
