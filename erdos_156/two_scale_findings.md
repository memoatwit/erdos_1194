# Two-scale and architecture-invariance findings (#156, May 17)

Phase 9 closing note.  Sequel to `overnight_structure_summary.md`.

## Strategic question

Can a shifted-template construction (template `B` together with all shifts
`A = s + B` that are maximal Sidon in `[1, N]`) reach Erdős's conjectured
`m(N) = O(N^{1/3})` upper bound?

## Result

**Empirically no.**  The architecture saturates at

```text
L  ≈  C · k^3 / (log k)^2,   with C ∈ [0.9, 1.2],
```

where `L` is the longest admissible blocker interval `[L, R] ⊂ W(B)` (i.e.
`L ≤ 0` and `R ≥ max(B)`) and `k = |B|`.  Inverting gives shifted-template
witnesses for every

```text
m(N)  ≤  k(N)  ~  ( N (log N)^2 )^{1/3},
```

strictly worse than Ruzsa's `(N log N)^{1/3}` ceiling, and short of the
conjectured `N^{1/3}` by a `(log N)^{2/3}` factor.

## Data

### A — broad-seed core-4 family (same architecture, varied k)

`B24_new = [0, 15, 35, 38, 39, 44, 95, 105, 163, 180, 196, 283, 296, 310,
404, 478, 519, 694, 792, 845, 864, 1019, 1030, 1051]`.  Extension by beam
search and one-swap local optimization:

| k | L | L/k³ | L·log²(k)/k³ |
|---:|---:|---:|---:|
| 18 | 758 | 0.130 | 1.086 |
| 20 | 968 | 0.121 | 1.086 |
| 24 | 1490 | 0.108 | 1.089 |
| 32 | 2912 | 0.089 | 1.067 |

Least-squares fit on log scale, `L ≈ A · k^3 / (log k)^p`:
A = 1.20, p = 2.09, R² = 0.9989.

### B — naive two-scale `aS + C` (FAILED)

Taking a Singer perfect-difference set `S ⊂ Z_{q²+q+1}` of size `q+1` and a
small Sidon core `C` (e.g. `[0,1,3,7]`), the Minkowski sum `aS + C` is
**not Sidon** for any `a`: every tile contains the same `Δ(C)` differences,
so each difference in `Δ(C)` is repeated `|S|` times.  Verified for q=3,
a∈[15,30] and several cores; always Sidon-breaking.

### B′ — per-anchor-varying two-scale (FAILED differently)

To break the duplicate-difference problem, assign each anchor `s_i` a *distinct*
small offset `d_i` from a fixed alphabet.  The result `B = {a s_i, a s_i + d_i}`
is Sidon for many parameter choices, but the templates are sparse: `max(B) ≈ aM ≈ aq²`,
while blocker events cluster around each tile leaving the middle of `[0, max(B)]`
empty.  At q=11, alphabet `{0,1,3,7,12,20}`, every tried `a` gave `k=17` and
the longest interval containing `0` was length 8–9 — admissible interval is
non-existent.  See `two_scale_varying.py`.

### C′ — architecture-invariance across diverse seeds at k=12

Beam search (no overlap, `x-factor = 1.0`, beam width 16) starting from
five genuinely different seeds of size 6:

| seed | seed-type | L (at k=12) | L/k³ | L·log²(k)/k³ |
|---|---|---:|---:|---:|
| `[0,1,3,9]` + 2 extensions | Singer q=3 | 281 | 0.163 | 1.004 |
| `[0,1,3,13,32,36,43,52]` truncated | Singer q=7 | 296 | 0.171 | 1.058 |
| `[0,3,10,11,16,28]` | random Sidon | 275 | 0.159 | 0.983 |
| `[0,8,22,26,27,29]` | random Sidon | 268 | 0.155 | 0.958 |
| `[0,3,5,9,24,25]` | random Sidon | 264 | 0.153 | 0.943 |

Spread of `L·log²(k)/k³` at k=12: width **0.12**.  Combined with the
broad-seed values at k=18..32 (1.07-1.09), the full spread across all seeds
and all k is **0.94 to 1.09 — width 0.15**.

## Interpretation

The seed barely matters.  Once the beam-style "extend one element to maximize
admissible interval / k³" procedure runs for a few steps, every starting
structure relaxes into the same scaling envelope.  This is consistent with
the anchor-cover decomposition (`anchor_cover_analysis.md`): the construction
spends roughly equal effort on core-anchor and anchor-anchor difference
events, so the local geometry of the seed is washed out within a few rounds.

This is not a proof.  There are at least three loopholes:

1. The beam architecture is greedy; a non-local search (e.g. CP-SAT,
   exact branch-and-bound) might find templates outside the beam envelope.
2. We have not considered all template-style constructions, only those of
   the form "compute `W(B)` and find the longest admissible interval".
   A construction that targets a different invariant might fare better.
3. The fit is on 4-5 datapoints in a small `k` range.  Even at `k = 32`
   the absolute number of templates evaluated by local search is large
   but the family is narrow.

## Recommendation

For #156, the next moves are:

1. **Stop spending serious time on shifted-template constructions.** Witness
   coverage to `N = 1490` is already in hand, and exact `m(N)` is known for
   `N ≤ 125`.
2. **Two productive directions remain open:**
   - Continue exact finite data at `N=130`: size 8 is feasible by shifted
     template, but `k=7` is not certified.
   - Improve the *lower bound*.  The known $\Omega(N^{1/3})$ greedy bound has
     no known matching upper-bound construction below Ruzsa.  Even an
     improvement from `Ω(N^{1/3})` to `Ω(N^{1/3} log^{1/4} N)` would be
     publishable and would directly disprove the strongest form of
     Erdős's conjecture.
3. **Pivot to a related problem.**  Erdős #40 (`B_3` set growth) shares
     verification machinery; the existing solver in `erdos_1194/erdos_40/`
     could be brought back.

## Files added in this round

- `two_scale_plan.md`             — design notes for two-scale construction.
- `two_scale_template.py`         — Singer / Erdős-Turán anchor library and
  composition framework.
- `two_scale_varying.py`          — per-anchor-distinct-offset variant.
- `results/template_two_scale_156_sweep.json` — naive `aS+C` sweep (empty,
  expected).
- `results/template_two_scale_156_singer_seed_q3.json`
- `results/template_two_scale_156_singer_seed_q3_k14.json`
- `results/template_two_scale_156_singer_seed_q7_k14.json`
- `results/template_two_scale_varying_156_sweep.json` (empty, expected).
- `results/c_prime_seed1.json`, `c_prime_seed2.json`, `c_prime_seed3.json`
  — diverse-seed beams.
- `results/template_beam_156_new_seed_core4_k28.json`,
  `template_beam_156_new_seed_core4_k32.json`,
  `template_local_opt_156_new_seed_core4_k32.json` — k=28/32 broad-seed
  diagnostic runs.
- `two_scale_findings.md`         — this note.
