# #156 frontier session — N=120

## Session result

**Resolved: $m(120)=8$.**

- Size 8 witness:
  `[43, 44, 56, 60, 75, 78, 86, 115]`.
- The witness was verified by `python3 erdos_156/solve_156.py verify 120 ...`:
  it is Sidon and inclusion-maximal in `[1,120]`.
- The counting lower bound starts at $k=6$ for $N=120$.
- `search156_v3 120 6 2400` proved $k=6$ infeasible in 699.128 s.
- `search156_v4 120 7 2400 f f` proved every canonical first-element slice
  `f=1,...,60` infeasible. This covers all size-7 witnesses up to reflection,
  since any witness or its reflection has first element at most
  `floor((120+1)/2)=60`.

The detailed exact log is in `results/exact_156_N120.json`.

## Heuristic notes

Size 8 was harder but still findable:

- `python3 erdos_156/solve_156.py hunt 120 8 50000` found
  `[43, 44, 56, 60, 75, 78, 86, 115]` after 7739 trials.
- `erdos_156/search156_v3 120 8 900` independently found
  `[1, 7, 51, 55, 58, 69, 84, 100]` in 628.528 s.

## Interpretation

The size-8 plateau now runs from $N=105$ through $N=120$.

- $m(105)=m(110)=m(115)=m(120)=8$.
- The ratio $m(N)/N^{1/3}$ is about 1.6219 at $N=120$.
- The verified hunt witness blocks 111 outside points by existing differences
  and has 1 midpoint-only blocker.

## What to try next

1. **Move to $N=125$**. The counting lower bound still starts at $k=6$; first
   find an 8-witness, then decide whether to spend the full exact $k=7$ split.
2. **Watch the cost curve.** The $N=120,k=7$ certificate took substantially
   longer than $N=115$; exact frontier pushing is now expensive.
3. **Mine the size-8 witnesses.** The witnesses at $N=110,115,120$ are likely
   more valuable for construction than another few isolated exact values.

## Files updated

- `results/exact_156_N120.json`: detailed exact certificate for $m(120)=8$.
- `results/exact_156.json` and `results/exact_156_summary.md`: exact table
  extended through $N=120$.
- `SESSION_HANDOFF.md` and `phase9_summary.md`: frontier moved to $N=125$.
- This session-handoff: `SESSION_N120.md`.
