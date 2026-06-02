# #156 frontier session — N=115

## Session result

**Resolved: $m(115)=8$.**

- Size 8 witness:
  `[1, 3, 43, 47, 53, 61, 66, 96]`.
- The witness was verified by `python3 erdos_156/solve_156.py verify 115 ...`:
  it is Sidon and inclusion-maximal in `[1,115]`.
- `search156_v3 115 5 300` proved $k=5$ infeasible in 0.001 s.
- `search156_v3 115 6 1800` proved $k=6$ infeasible in 642.764 s.
- `search156_v4 115 7 1800 f f` proved every canonical first-element slice
  `f=1,...,58` infeasible. This covers all size-7 witnesses up to reflection,
  since any witness or its reflection has first element at most
  `floor((115+1)/2)=58`.

The detailed exact log is in `results/exact_156_N115.json`.

## Heuristic notes

Size 8 was still easy enough to find:

- `erdos_156/search156_v3 115 8 600` found
  `[1, 3, 43, 47, 53, 61, 66, 96]` in 65.273 s.
- `python3 erdos_156/solve_156.py hunt 115 8 50000` independently found
  `[17, 40, 43, 47, 56, 76, 78, 90]` after 2245 trials.

## Interpretation

The size-8 plateau continues from $N=105$ through $N=115$.

- $m(105)=m(110)=m(115)=8$.
- The ratio $m(N)/N^{1/3}$ is about 1.6451 at $N=115$.
- The main verified witness has 102 points blocked by existing differences
  and 5 midpoint-only blockers.

## What to try next

1. **Move to $N=120$** with the same pipeline. Find an 8-witness first; if
   that succeeds, run the exact $k=7$ split over `1..60`.
2. **Start comparing size-8 witnesses structurally.** The known witnesses at
   $N=105,110,115$ have noticeably different blocking profiles, which may be
   useful for a construction attempt.
3. **Watch exact-search cost.** The $k=7$ certificate is getting heavier; if
   $N=120$ becomes too slow, pivot toward structural construction.

## Files updated

- `results/exact_156_N115.json`: detailed exact certificate for $m(115)=8$.
- `results/exact_156.json` and `results/exact_156_summary.md`: exact table
  extended through $N=115$.
- `SESSION_HANDOFF.md` and `phase9_summary.md`: frontier moved to $N=120$.
- This session-handoff: `SESSION_N115.md`.
