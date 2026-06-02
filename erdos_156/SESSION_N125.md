# #156 frontier session — N=125

## Session result

**Solved.** Current certified value:

\[
m(125)=8.
\]

What is known:

- The counting lower bound starts at $k=6$ for $N=125$.
- `search156_v3 125 6 3000` proved $k=6$ infeasible in 608.140 s.
- A resumable `search156_v4` first-element split proved $k=7$ infeasible for
  all canonical first elements $1,\ldots,63$.  Reflection makes this complete:
  every size-7 witness or its reflection has first element at most
  $\lfloor(125+1)/2\rfloor=63$.
- The k=7 split used 63 chunks, searched 2,810,668,688 nodes, and reported
  16,522.156 total chunk-seconds.  Details are in
  `results/exact_156_N125_k7_split.json`.
- Size 8 is feasible. Witness:
  `[5, 42, 45, 49, 64, 76, 77, 87]`.
- The size-8 witness was found by `repair_125_k8.py` and verified by
  `python3 erdos_156/solve_156.py verify 125 5 42 45 49 64 76 77 87`.
- A second verified size-8 witness is
  `[38, 48, 49, 61, 76, 80, 83, 120]`.
- Size 9 is also feasible, but now superseded as the best upper bound. Witness:
  `[18, 42, 51, 59, 71, 81, 86, 87, 118]`.

What is not known:

- `search156_v3 125 8 1200` timed out after 1200.330 s with no witness.
- `python3 erdos_156/solve_156.py hunt 125 8 50000` was stopped after a long
  run with no certificate, before the later repair search found a witness.

The detailed frontier log is in `results/frontier_156_N125.json`.

## Interpretation

The size-8 plateau now has a witness through \(N=125\):

- $m(105)=m(110)=m(115)=m(120)=8$.
- At $N=125$, size 8 is feasible:
  `[5, 42, 45, 49, 64, 76, 77, 87]`.
- The k=7 certificate rules out size 7, so this proves \(m(125)=8\).
- The previous pipeline missed size 8, so seeded repair/local search is now a
  useful witness engine alongside the exact DFS proof engine.

## What to try next

1. **Move exact frontier to $N=130$ if certification matters.** The shifted
   template gives size 8 at \(N=130\); exact work would need to rule out k=7.
2. **Mine the size-8 witnesses structurally.** Compare the witnesses at
   $N=105,110,115,120,125$ and look for a reusable difference-cover pattern.
3. **Continue construction work.** The finite exact frontier is helpful, but
   the Erdős problem still needs an asymptotic construction.

## Files updated

- `results/frontier_156_N125.json`: solved frontier value and logs.
- `results/exact_156_N125.json`: exact summary for \(N=125\).
- `results/exact_156_N125_k7_split.json`: detailed k=7 first-element split.
- `run_split_exact.py`: resumable wrapper for `search156_v4` split runs.
- `results/repair_156_N125_k8.json`: repair-search witness and verification.
- `repair_125_k8.py`: seeded one-swap/beam repair search for size-8 witnesses.
- `SESSION_HANDOFF.md` and `phase9_summary.md`: frontier state updated.
- This session-handoff: `SESSION_N125.md`.
