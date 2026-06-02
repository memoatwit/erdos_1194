# #156 frontier session — N=105

## Session result

**Resolved: $m(105)=8$.**

- Size 8 witness:
  `[1, 3, 13, 34, 47, 50, 58, 88]`.
- The witness was verified by `python3 erdos_156/solve_156.py verify 105 ...`:
  it is Sidon and inclusion-maximal in `[1,105]`.
- `search156_v3 105 5 300` proved $k=5$ infeasible in 0.081 s.
- `search156_v3 105 6 900` proved $k=6$ infeasible in 339.962 s.
- `search156_v4 105 7 450 f f` proved every canonical first-element slice
  `f=1,...,53` infeasible. This covers all size-7 witnesses up to reflection,
  since any witness or its reflection has first element at most
  `floor((105+1)/2)=53`.

The detailed exact log is in `results/exact_156_N105.json`.

## Previous heuristic work

## Heuristic hunt results at $N=105, k=7$

Several runs converged to near-misses but no witness:

| seeds tried | trials each | best blocked | sample near-miss | addable |
|---|---|---:|---|---|
| 1 (default) | 1500 | 100/105 | varies | 5 |
| 8 seeds × 200 trials | 1600 total | 100/105 max | `[33, 47, 52, 53, 55, 84, 99]` (seed 1234) | `{12, 17, 29, 88, 95}` |

Tight-pair-enforced hunt (each trial seeds with `(a, a+gap)` for
`gap ∈ {1, 2}`): same plateau at 99–100/105 blocked. The tight-pair
heuristic, which fits every known witness through $N=100$, does not
unlock $N=105$.

**Local-repair from $N=100$ witness** `[8, 42, 44, 48, 56, 59, 83]`:
- 1-swap (all $(7 \times 105)$ neighborhoods): no maximal-in-$[1,105]$
  result.
- 2-swap (99,813 swaps explored before time-out): no result.

## Interpretation

The exact search confirms the second outcome from the earlier fork:
the `7`-plateau breaks at $N=105$.

- $m(100)=7$ but $m(105)=8$.
- The ratio $m(N)/N^{1/3}$ jumps from about 1.5081 at $N=100$ to about
  1.6957 at $N=105$.
- This is still consistent with $N^{1/3}$-scale behavior, but the finite
  data is now visibly lumpy at plateau boundaries.

The failure of the tight-pair heuristics was a real signal here: no size-7
witness existed, not just a hard-to-find non-tight one.

## What to try next

1. **Move to $N=110$** with the same pipeline: prove $k=7$ or find a
   size-8 witness quickly, then decide whether $m(110)=8$ or higher.
2. **Tightness-relaxed hunt**: drop the tight-pair requirement and bias
   toward a near-arithmetic-progression structure (Singer-like). Witness
   at $N = 70$ has consecutive gaps $\{15, 4, 2, 11, 7, 5\}$ — quite
   spread.
3. **Pivot to construction**: the empirical ratio $m(N)/N^{1/3}$
   continues to hover in $[1.46, 1.71]$ with no clear asymptote. A
   probabilistic / algebraic construction proving
   $m(N) \leq C N^{1/3}$ for an explicit $C$ is the natural research
   target.

## Files updated

- `hunt_tight_pair.py` (new): tight-pair-constrained random hunt.
- `search156_v3_local`, `search156_v4_local`: rebuilt binaries
  using `g++` (the checked-in binaries were `clang++`-built and don't
  run in this VM).
- `results/exact_156_N105.json`: detailed exact certificate for $m(105)=8$.
- `results/exact_156.json` and `results/exact_156_summary.md`: exact table
  extended through $N=105$.
- This session-handoff: `SESSION_N105.md`.
