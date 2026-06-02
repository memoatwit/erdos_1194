# #156 frontier session — N=110

## Session result

**Resolved: $m(110)=8$.**

- Size 8 witness:
  `[11, 46, 50, 53, 59, 75, 83, 93]`.
- The witness was verified by `python3 erdos_156/solve_156.py verify 110 ...`:
  it is Sidon and inclusion-maximal in `[1,110]`.
- `search156_v3 110 5 300` proved $k=5$ infeasible in 0.046 s.
- `search156_v3 110 6 1200` proved $k=6$ infeasible in 532.595 s.
- `search156_v4 110 7 900 f f` proved every canonical first-element slice
  `f=1,...,55` infeasible. This covers all size-7 witnesses up to reflection,
  since any witness or its reflection has first element at most
  `floor((110+1)/2)=55`.

The detailed exact log is in `results/exact_156_N110.json`.

## Heuristic notes

Size 8 was easy:

- `python3 erdos_156/solve_156.py hunt 110 8 50000` found
  `[11, 46, 50, 53, 59, 75, 83, 93]` after 166 trials.
- `erdos_156/search156_v3 110 8 300` independently found
  `[1, 3, 19, 42, 49, 52, 53, 107]` in 22.374 s.

Size 7 was not visible heuristically:

- `python3 erdos_156/solve_156.py hunt 110 7 50000` found no witness.
- Best near-miss blocked 105/110:
  `[11, 38, 40, 46, 58, 71, 74]`.
- Addable points for that near-miss:
  `{1, 16, 88, 95, 97}`.

## Interpretation

The size-8 plateau continues from $N=105$ to $N=110$.

- $m(105)=8$ and $m(110)=8$.
- The ratio $m(N)/N^{1/3}$ is about 1.6697 at $N=110$.
- The size-8 witness at $N=110$ blocks all outside points through existing
  differences alone; there are no midpoint-only blockers in its verification
  profile.

## What to try next

1. **Move to $N=115$** with the same pipeline: find an 8-witness first, then
   decide whether exact $k=7$ search is needed.
2. **Compare the $N=105$ and $N=110$ size-8 witnesses.** The $N=110$ witness
   is cleaner by blocking profile, so it may be better for structural
   generalization.
3. **Pivot to construction** if the exact frontier starts costing more than
   it reveals.

## Files updated

- `results/exact_156_N110.json`: detailed exact certificate for $m(110)=8$.
- `results/exact_156.json` and `results/exact_156_summary.md`: exact table
  extended through $N=110$.
- `SESSION_HANDOFF.md` and `phase9_summary.md`: frontier moved to $N=115$.
- This session-handoff: `SESSION_N110.md`.
