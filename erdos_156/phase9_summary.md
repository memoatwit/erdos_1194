# Phase 9 — Erdős Problem #156, session 1

## What we built

Files:

- `erdos_156/solve_156.py`
- `erdos_156/search156.cpp`

The first solver is self-contained because `ortools` is not installed in this
workspace. It uses bitset/backtracking rather than CP-SAT. Session 2 added a
small C++ fixed-size exact checker; this is now the fastest way to prove
infeasibility for a specific \(N,k\).

Implemented:

- `is_sidon(A, N=None)`
- `is_maximal_sidon(A, N)`
- `blocking_profile(A, N)`
- random/sequential greedy builders for quick maximal Sidon upper bounds
- exact search for
  \[
  m(N)=\min\{|A|:A\subset[1,N]\text{ is maximal Sidon}\}
  \]
  by enumerating Sidon sets by cardinality and testing maximality at leaves

Results are written to:

- `erdos_156/results/exact_156.json`
- `erdos_156/results/exact_156_summary.md`
- per-\(N\) files `erdos_156/results/exact_156_N{N}.json`

## Exact data

Exact values are now known for \(N=5,10,\ldots,125\). The latest value is
\(m(125)=8\): a complete first-element split ruled out \(k=7\), and a size-8
maximal Sidon witness is `[5, 42, 45, 49, 64, 76, 77, 87]`.

| \(N\) | status | \(m(N)\) | witness |
|---:|---|---:|---|
| 5 | solved | 3 | `[1, 2, 4]` |
| 10 | solved | 3 | `[2, 5, 6]` |
| 15 | solved | 4 | `[1, 2, 4, 12]` |
| 20 | solved | 4 | `[1, 8, 12, 13]` |
| 25 | solved | 5 | `[1, 2, 4, 10, 23]` |
| 30 | solved | 5 | `[1, 4, 11, 15, 17]` |
| 35 | solved | 5 | `[1, 12, 13, 18, 22]` |
| 40 | solved | 5 | `[3, 16, 17, 24, 26]` |
| 45 | solved | 6 | `[1, 2, 4, 19, 23, 31]` |
| 50 | solved | 6 | `[1, 2, 15, 22, 24, 27]` |
| 55 | solved | 6 | `[1, 8, 22, 25, 31, 44]` |
| 60 | solved | 6 | `[1, 18, 21, 30, 36, 40]` |
| 65 | solved | 6 | `[9, 25, 26, 32, 40, 45]` |
| 70 | solved | 7 | `[8, 23, 27, 29, 40, 47, 52]` |
| 75 | solved | 7 | `[15, 24, 25, 39, 42, 47, 58]` |
| 80 | solved | 7 | `[25, 34, 36, 40, 48, 64, 65]` |
| 85 | solved | 7 | `[23, 33, 44, 45, 58, 61, 63]` |
| 90 | solved | 7 | `[13, 29, 36, 37, 51, 57, 62]` |
| 95 | solved | 7 | `[3, 37, 39, 43, 51, 54, 78]` |
| 100 | solved | 7 | `[8, 42, 44, 48, 56, 59, 83]` |
| 105 | solved | 8 | `[1, 3, 13, 34, 47, 50, 58, 88]` |
| 110 | solved | 8 | `[11, 46, 50, 53, 59, 75, 83, 93]` |
| 115 | solved | 8 | `[1, 3, 43, 47, 53, 61, 66, 96]` |
| 120 | solved | 8 | `[43, 44, 56, 60, 75, 78, 86, 115]` |
| 125 | solved | 8 | `[5, 42, 45, 49, 64, 76, 77, 87]` |

The ratios \(m(N)/N^{1/3}\) for the solved range stay roughly between 1.46
and 1.71 after \(N=20\). This is consistent with \(N^{1/3}\)-scale behavior
but, of course, finite data alone is not evidence of the asymptotic theorem.

## Shifted-template parametrization

The clearest finite construction now has a reusable template

```text
B = [0, 40, 60, 61, 63, 67, 96, 112]
```

For a template \(B\), define

\[
W(B)=B\cup(B+\Delta(B))\cup(B-\Delta(B))\cup\text{integer midpoints}(B).
\]

Then \(A=s+B\) is maximal in \([1,N]\) exactly when \(A\subset[1,N]\) and
\([1-s,N-s]\subset W(B)\).  For the template above, \(W(B)\) contains the full
interval \([-7,136]\).  Since \(\max B=112\), every shift satisfying

\[
\max(1,N-136)\le s\le \min(8,N-112)
\]

gives a maximal Sidon set.  Hence this single template certifies size-8
maximal Sidon sets for every \(N=113,\ldots,144\), and no shift of this
template works at \(N=145\).

The next two one-point extensions also work:

| size | template max | blocker interval | covered \(N\) |
|---:|---:|---|---|
| 9 | 144 | `[-12,148]` | 145-161 |
| 10 | 149 | `[-29,157]` | 150-187 |

Thus shifted templates now give construction-based witnesses for every
\(N=113,\ldots,187\).  The interval-length ratios to \(k^3\) decrease across
sizes 8, 9, and 10, so this is finite structural progress rather than an
asymptotic construction.

The greedy continuation script `extend_template_chain.py` pushes this same
rule to size 20 and covers through \(N=788\), but the endpoint ratio is only
\(788/20^3\approx0.0985\).  This is useful deterministic witness generation,
but the data argues against greedy one-point endpoint extension as the proof
mechanism.

The beam search `beam_template_search.py` improves the finite result.  With
overlap required between consecutive covered ranges, a width-120 beam to
size 20 finds a path whose covered-range union is \(N=113,\ldots,913\).  The
final size-20 template covers \(N=701,\ldots,913\), giving endpoint ratio
\(913/20^3\approx0.1141\).  A freer no-overlap beam to size 16 did not improve
the density, and a one-swap local pass around the best size-20 template found
no improvement up to replacement value 1000.

The architecture-diversified search found the alternative seed
`[0,20,35,38,39,44,46,95]`; its size-20 beam path has covered union
\(N=96,\ldots,922\).  Local optimization then replaced `111` with `681`,
giving a size-20 local optimum covering \(N=682,\ldots,967\), with endpoint
ratio \(967/20^3=0.120875\).  Combining the beam path and this local template
gives deterministic shifted-template witnesses for every \(N=96,\ldots,967\).

The anchor-cover model has now been checked directly.  Freezing the 7-mark
core `[0,20,35,38,39,44,46]` and searching only for anchors gives a size-20
beam chain with covered union \(N=47,\ldots,935\).  Source decomposition of
the local optimum over `[-273,693]` shows comparable use of core-anchor and
anchor-anchor differences: 2637 versus 2565 blocker events.  Thus a scalable
formula likely needs structured anchor layers whose pairwise differences fill
gaps, not just anchors translating a fixed core-difference set.

May 17 continuation: a broader core-4 seed
`[0,15,35,38,39,44,46,95]` improved the record after extension and local
optimization.  The new size-20 template
`[0,15,35,38,39,44,46,95,114,136,157,202,238,288,346,373,413,507,594,647]`
has `W(B)` containing `[-225,742]`, covering \(N=648,\ldots,968\), so the
size-20 endpoint ratio is now \(968/20^3=0.121\).  Extending the same seed to
k=24 and running two local passes produced
`[0,15,35,38,39,44,95,105,163,180,196,283,296,310,404,478,519,694,792,845,864,1019,1030,1051]`,
with `W(B)` containing `[-361,1128]`, covering \(N=1052,\ldots,1490\).  In
combination with the beam ancestry, shifted-template witnesses now cover
every \(N=96,\ldots,1490\).

A further diagnostic extension of the same broad-seed/local architecture to
k=32 produced
`[0,15,35,38,39,44,95,105,163,180,196,283,296,310,404,478,519,694,792,864,1019,1030,1051,1153,1183,1352,1438,1483,1909,1928,1956,2068]`,
with `W(B)` containing `[-766,2145]`, covering \(N=2069,\ldots,2912\).  The
quantity \(L\log^2(k)/k^3\) remains close to 1.07 at k=32, strengthening the
case that this architecture follows a \(k^3/\log^2 k\)-type envelope rather
than a true \(k^3\) envelope.

The first two-scale product attempt `B=a*S+C` was also tested.  It fails as a
literal product because using the same nontrivial core in multiple macro tiles
repeats core-core differences, so the resulting set is usually not Sidon.
Singer sets may still be useful as beam seeds, but a genuine two-scale
construction will need varied or perturbed cores across macro tiles.

See `template_parametrization.md`, `parametrize_template.py`, and
`results/template_156_parametrized.json`.

## Blocking-profile observation

For the first witnesses, almost every outside point is blocked by matching an
already-used difference. Midpoint/symmetric collisions are rare.

Examples:

- \(N=50\), witness `[1, 2, 15, 22, 24, 27]`:
  - in \(A\): 6
  - blocked by existing difference: 44
  - blocked by symmetric collision: 0
  - addable: 0
- \(N=60\), witness `[1, 18, 21, 30, 36, 40]`:
  - in \(A\): 6
  - blocked by existing difference: 53
  - blocked by symmetric collision: 1
  - addable: 0

This suggests the constructive target can be phrased as:

> Build a small Sidon set whose existing differences, translated by the set
> itself, cover all of `[1,N]`.

The midpoint blockers are helpful but not the main phenomenon in these small
examples.

## Search bottleneck history

The first hard case was \(N=65\):

- counting lower bound starts at \(k=5\);
- the solver proved \(k=5\) infeasible in about 13 seconds;
- a coverage-first randomized hunt found a size-6 witness
  `[9, 25, 26, 32, 40, 45]`;
- therefore \(m(65)=6\).

The next hard case was \(N=70\):

- counting lower bound starts at \(k=5\);
- the Python solver proved \(k=5\) infeasible in about 25 seconds;
- greedy finds a size-7 maximal Sidon set;
- a 50,000-trial hunt for size 6 found no witness; best near-miss blocks
  68 of 70 points with witness `[17, 24, 28, 33, 46, 47]`, leaving
  `7` and `67` addable;
- DFS with coverage ordering also timed out on \(k=6\).

Session 3 added `search156.cpp`, a small C++ exact checker. It proved
\(N=70,k=6\) infeasible in about 32 seconds, giving \(m(70)=7\). The same
checker then proved \(k=6\) infeasible for \(N=75,80,85,90\), while the Python
hunt/greedy routines supplied size-7 witnesses. Hence \(m(N)=7\) for
\(N=70,75,80,85,90\).

Session 4 added `search156_v3.cpp`, which maintains the unblocked/addable set
incrementally. This resolved \(N=95\):

- \(N=95,k=5\): infeasible.
- \(N=95,k=6\): infeasible in 160.86s.
- \(N=95,k=7\): feasible in 240.385s with witness
  `[3, 37, 39, 43, 51, 54, 78]`.
- Therefore \(m(95)=7\).

The next frontier was \(N=100\).

- \(N=100,k=5\): infeasible.
- \(N=100,k=6\): infeasible in 229.097s.
- \(N=100,k=7\): v3 exact search timed out after 600s, but v4 split search
  found a witness with first element 8:
  `[8, 42, 44, 48, 56, 59, 83]`.
- \(N=100,k=8\): feasible with witness
  `[4, 26, 37, 38, 43, 57, 64, 73]`.
- Therefore \(m(100)=7\).

For \(N=100,k=7\), 50K Python hunt trials found no witness. Best near-miss:
`[28, 30, 46, 49, 57, 71, 83]`, leaving addable points `13` and `88`.
A radius-3 local repair tried 5,095,160 nearby sets and found no witness; best
alternate near-miss was `[30, 36, 47, 55, 57, 71, 83]`, leaving `7` and `86`.

The next frontier was \(N=105\).

- \(N=105,k=5\): infeasible in 0.081 s.
- \(N=105,k=6\): infeasible in 339.962 s.
- \(N=105,k=7\): v4 split search proved every canonical first element
  \(1,\ldots,53\) infeasible. This is complete up to reflection.
- \(N=105,k=8\): feasible with witness
  `[1, 3, 13, 34, 47, 50, 58, 88]`.
- Therefore \(m(105)=8\).

The next frontier was \(N=110\).

- \(N=110,k=5\): infeasible in 0.046 s.
- \(N=110,k=6\): infeasible in 532.595 s.
- \(N=110,k=7\): v4 split search proved every canonical first element
  \(1,\ldots,55\) infeasible. This is complete up to reflection.
- \(N=110,k=8\): feasible with witness
  `[11, 46, 50, 53, 59, 75, 83, 93]`.
- Therefore \(m(110)=8\).

The next frontier was \(N=115\).

- \(N=115,k=5\): infeasible in 0.001 s.
- \(N=115,k=6\): infeasible in 642.764 s.
- \(N=115,k=7\): v4 split search proved every canonical first element
  \(1,\ldots,58\) infeasible. This is complete up to reflection.
- \(N=115,k=8\): feasible with witness
  `[1, 3, 43, 47, 53, 61, 66, 96]`.
- Therefore \(m(115)=8\).

The next frontier was \(N=120\).

- \(N=120,k=6\): infeasible in 699.128 s.
- \(N=120,k=7\): v4 split search proved every canonical first element
  \(1,\ldots,60\) infeasible. This is complete up to reflection.
- \(N=120,k=8\): feasible with witness
  `[43, 44, 56, 60, 75, 78, 86, 115]`.
- Therefore \(m(120)=8\), and the next frontier is \(N=125\).

The next frontier attempt was \(N=125\).

- \(N=125,k=6\): infeasible in 608.140 s.
- \(N=125,k=7\): a resumable v4 first-element split proved every canonical
  first element \(1,\ldots,63\) infeasible. This is complete up to reflection.
  The split searched 2,810,668,688 nodes across 63 chunks, with 16,522.156
  total reported chunk-seconds.
- \(N=125,k=8\): v3 timed out after 1200.330 s with no witness.
- \(N=125,k=9\): feasible with witness
  `[18, 42, 51, 59, 71, 81, 86, 87, 118]`.
- A later seeded repair search found \(N=125,k=8\) feasible with witness
  `[5, 42, 45, 49, 64, 76, 77, 87]`. Independent verification reports
  `is_sidon: true`, `is_maximal_sidon: true`, and blocking profile
  `{in_A: 8, existing_difference: 116, symmetric_collision: 1, addable: 0}`.
- Therefore \(m(125)=8\).

Promising improvements:

1. Add stronger DFS pruning using upper bounds on how many still-unblocked
   positions can be blocked by the remaining slots.
2. Compress the MILP maximality encoding; the first SciPy/HiGHS model is
   correct but too large at \(N=70,k=6\) (about 226k binary variables and
   679k constraints).
3. Use the C++ checker as the proof engine for fixed-size infeasibility, and
   the Python `hunt` mode as the witness engine for the next size.
4. If `ortools` becomes available, implement the CP-SAT formulation from
   `phase9_plan.md`, likely with lazy/blocker generation.

## Session 2 additions

Updated `erdos_156/solve_156.py` with:

- `hunt` mode: coverage-first randomized construction for fixed \(N,k\);
- coverage-ordered DFS option for harder fixed-size searches;
- `milp` mode: SciPy/HiGHS feasibility model for fixed \(N,k\), encoding
  Sidon and maximality directly.

The MILP model passed a sanity test at \(N=10,k=3\), producing a valid maximal
Sidon witness `[4, 5, 7]`. At \(N=70,k=6\), the uncompressed model hit its time
limit without a certificate.

## Session 3 additions

Added `erdos_156/search156.cpp`.

It is an exact C++ fixed-size search using the same Sidon and maximality logic
as the Python verifier. Build command:

```bash
clang++ -O3 -std=c++17 erdos_156/search156.cpp -o erdos_156/search156
```

The compiled binary is ignored by `erdos_156/.gitignore`.

Key commands:

```bash
erdos_156/search156 70 6 300
erdos_156/search156 75 6 300
erdos_156/search156 80 6 300
erdos_156/search156 85 6 300
erdos_156/search156 90 6 300
```

All five returned `infeasible`. Together with size-7 witnesses, this extends
the exact table through \(N=90\).

## Session 4 additions

Added `erdos_156/search156_v3.cpp`.

v3 keeps an incremental bitmask of addable/unblocked positions, making coverage
pruning cheap enough to use at every node. Build command:

```bash
clang++ -O3 -std=c++17 erdos_156/search156_v3.cpp -o erdos_156/search156_v3
```

Resolved \(N=95\) and moved the frontier to \(N=100,k=7\).

## Session 5 additions

Added `erdos_156/search156_v4.cpp`, which is v3 plus first-element range
splitting:

```bash
clang++ -O3 -std=c++17 erdos_156/search156_v4.cpp -o erdos_156/search156_v4
```

For \(N=100,k=7\), v4 proved first elements 1 through 7 infeasible and found
witnesses at first elements 8 and 9. The first witness proves \(m(100)=7\):

```bash
erdos_156/search156_v4 100 7 300 8 8
```

returned `[8, 42, 44, 48, 56, 59, 83]`.

## Session 6 additions

Resolved \(N=105\). The key commands were:

```bash
erdos_156/search156_v3 105 5 300
erdos_156/search156_v3 105 6 900
for f in $(seq 1 53); do erdos_156/search156_v4 105 7 450 "$f" "$f"; done
erdos_156/search156_v3 105 8 300
```

The exact table now reaches \(N=105\), with \(m(105)=8\).

## Session 7 additions

Resolved \(N=110\). The key commands were:

```bash
erdos_156/search156_v3 110 5 300
erdos_156/search156_v3 110 6 1200
for f in $(seq 1 55); do erdos_156/search156_v4 110 7 900 "$f" "$f"; done
python3 erdos_156/solve_156.py hunt 110 8 50000
```

The exact table now reaches \(N=110\), with \(m(110)=8\).

## Session 8 additions

Resolved \(N=115\). The key commands were:

```bash
erdos_156/search156_v3 115 5 300
erdos_156/search156_v3 115 6 1800
for f in $(seq 1 58); do erdos_156/search156_v4 115 7 1800 "$f" "$f"; done
erdos_156/search156_v3 115 8 600
```

The exact table now reaches \(N=115\), with \(m(115)=8\).

## Session 9 additions

Resolved \(N=120\). The key commands were:

```bash
erdos_156/search156_v3 120 6 2400
for f in $(seq 1 60); do erdos_156/search156_v4 120 7 2400 "$f" "$f"; done
python3 erdos_156/solve_156.py hunt 120 8 50000
```

The exact table now reaches \(N=120\), with \(m(120)=8\).

## Session 10 additions

Probed \(N=125\) and hit the next wall. The key commands were:

```bash
erdos_156/search156_v3 125 6 3000
erdos_156/search156_v3 125 8 1200
python3 erdos_156/solve_156.py hunt 125 9 50000
```

The exact table remains solved through \(N=120\). At this point the certified
bracket was \(7 \le m(125) \le 9\).

## Session 11 additions

Added `erdos_156/repair_125_k8.py`, a targeted size-8 witness search. It
scores a fixed-size Sidon set by the exact blocked mask, starts from known
size-8 and size-9 witnesses, then applies one-swap repair and randomized
coverage-first rebuilds around the best states.

Key command:

```bash
python3 erdos_156/repair_125_k8.py 125 8 15 156
```

This found the size-8 witness `[5, 42, 45, 49, 64, 76, 77, 87]`, verified by:

```bash
python3 erdos_156/solve_156.py verify 125 5 42 45 49 64 76 77 87
```

Therefore the frontier improved to \(7 \le m(125) \le 8\). Exact
certification of \(m(125)=8\) required ruling out \(k=7\).

## Session 11b additions

Added `erdos_156/run_split_exact.py`, a resumable wrapper around
`search156_v4`, and ran:

```bash
python3 erdos_156/run_split_exact.py --N 125 --k 7 --workers 8 --output erdos_156/results/exact_156_N125_k7_split.json
```

The run proved all canonical first elements \(1,\ldots,63\) infeasible for
\(N=125,k=7\).  By reflection this is complete, so with the known size-8
witness we have \(m(125)=8\).  The split searched 2,810,668,688 nodes across
63 chunks.

## Session 12 additions

Ran structural mining rather than exact enumeration. Added:

- `erdos_156/mine_structure.py`
- `erdos_156/local_repair_156.py`
- `erdos_156/parametrize_template.py`
- `erdos_156/extend_template_chain.py`
- `erdos_156/beam_template_search.py`
- `erdos_156/search_template_architectures.py`
- `erdos_156/local_optimize_template.py`
- `erdos_156/analyze_anchor_cover.py`
- `erdos_156/structure_mining.md`
- `erdos_156/template_parametrization.md`
- `erdos_156/overnight_structure_summary.md`
- `erdos_156/results/structure_156.json`
- `erdos_156/results/template_156_size8_120_144.json`
- `erdos_156/results/template_156_parametrized.json`
- `erdos_156/results/template_156_size9_145_161.json`
- `erdos_156/results/template_156_size10_150_187.json`
- `erdos_156/results/template_chain_156_greedy.json`
- `erdos_156/results/template_beam_156_overlap_k20.json`
- `erdos_156/results/template_beam_156_free_k16.json`
- `erdos_156/results/template_architecture_search_156_core4_k16.json`
- `erdos_156/results/template_architecture_search_156_core5_k16.json`
- `erdos_156/results/template_beam_156_arch_seed_core4_k20.json`
- `erdos_156/results/template_local_opt_156_arch20.json`
- `erdos_156/results/template_local_opt_156_arch20_pass2.json`
- `erdos_156/results/template_anchor_cover_core7_k20.json`
- `erdos_156/results/template_anchor_cover_core7_free_k16.json`
- `erdos_156/results/anchor_cover_analysis_156.json`
- `erdos_156/anchor_cover_analysis.md`

Main finite pattern:

```bash
B = [0, 40, 60, 61, 63, 67, 96, 112]
```

The structural pass first found shifts for \(N=120,\ldots,144\).  The later
parametrization shows that \(W(B)\) contains the interval \([-7,136]\), so
every \(N=113,\ldots,144\) has some shift \(A=s+B\) that is a maximal Sidon
subset of \([1,N]\).  No shift of this size-8 template works at \(N=145\), but
the size-9 extension by `144` covers \(N=145,\ldots,161\), and the size-10
extension by `149` covers \(N=150,\ldots,187\).

A greedy continuation through size 20 covers \(N=551,\ldots,788\) at the last
row, but the normalized endpoint continues dropping.  The next search should
use beam/local moves to optimize interval length per \(k^3\), rather than
committing to the locally best endpoint append.

That beam/local check has now been run.  Beam improves finite coverage to
\(N=113,\ldots,913\) using sizes up to 20, but the endpoint ratio remains
downward-trending.  The next idea should be a different architecture, not just
more tuning of this append chain.

The first architecture-diversified search has also been run.  It found the
alternative seed `[0,20,35,38,39,44,46,95]`; its size-20 beam path has covered
union \(N=96,\ldots,922\), ending with \(N=618,\ldots,922\) at size 20.  The
endpoint ratio improves slightly to \(922/20^3=0.11525\).  This confirms that
seed diversification helps, though the gain is incremental.

The local optimizer then found one more improvement by replacing `111` with
`681`.  The improved size-20 template covers \(N=682,\ldots,967\), and a
second local pass found no further one-swap/annealing improvement.  The
geometry remains a dense small-difference core plus sparse anchor layers.

The anchor-cover decomposition shows the sparse anchors are doing more than
translating the core: anchor-anchor differences contribute nearly as many
blocker events as mixed core-anchor differences.  This points toward an
anchor-layer design problem as the next conceptual target.

Additional upper-bound data:

- \(N=130,k=8\): feasible.
- \(N=135,k=8\): feasible.
- \(N=140,k=8\): feasible.
- \(N=144,k=8\): feasible by the shifted template.
- \(N=145,k=8\): not found; best repair near-miss blocks 144/145.
- \(N=145,k=9\): feasible.

Exact values now remain certified through \(N=125\).  No lower-bound
certification beyond \(N=125\) was attempted.

## Commands used

Smoke test:

```bash
python3 erdos_156/solve_156.py verify 5 1 3
python3 erdos_156/solve_156.py solve 10 5
```

Main sweep:

```bash
python3 erdos_156/solve_156.py sweep 80 20
```

Additional session-2 commands:

```bash
python3 erdos_156/solve_156.py solve 65 20
python3 erdos_156/solve_156.py solve 70 30
python3 erdos_156/solve_156.py hunt 70 6 50000
python3 erdos_156/solve_156.py milp 10 3 20
python3 erdos_156/solve_156.py milp 70 6 180
```
