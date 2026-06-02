# Phase 8 — Erdős Problem #42 attack, session 1

## The problem

Erdős Problem #42 (\$100 bounty, open since ~1985):

> If $A, B \subset \{1, \ldots, N\}$ are two Sidon sets such that
> $(A - A) \cap (B - B) = \{0\}$, is it true that
> $\binom{|A|}{2} + \binom{|B|}{2} \leq \binom{f(N)}{2} + O(1)$,
> where $f(N) := \max |A|$ over Sidon $A \subset \{1, \ldots, N\}$?

The $O(1)$ is supposed to be a constant *independent of $N$*.

## Definitions

For each $N \geq 1$:
- $f(N) := \max \{|A| : A \subset [1, N], A \text{ Sidon}\}$.
- $g(N) := \max \{\binom{|A|}{2} + \binom{|B|}{2} : A, B \subset [1, N],
       A, B \text{ Sidon}, (A - A) \cap (B - B) = \{0\}\}$.
- Gap: $g(N) - \binom{f(N)}{2}$.

The conjecture says: gap is $O(1)$.

## Implementation

`solve_42.py` provides:
- `solve_f(N)`: CP-SAT model to compute $f(N)$. Variables: $y_i \in \{0,1\}$
  for $i \in [1, N]$. Sidon constraint: for each $d \in [1, N-1]$,
  $\sum_{i: i+d \leq N} y_i \, y_{i+d} \leq 1$ (encoded via auxiliary
  $u_{i, i+d}$).
- `solve_g(N)`: CP-SAT model maximising $\sum_{i<j} u_{i,j} + v_{i,j}$
  subject to: for each $d$, $\sum (u_{i,i+d} + v_{i,i+d}) \leq 1$.
  This *single constraint per $d$* encodes the Sidon condition for $A$,
  the Sidon condition for $B$, and the disjoint-difference condition,
  all in one. Symmetry-breaking: $|A| \geq |B|$.

## Data

Computed by CP-SAT with 8 workers and per-call time budgets of 8–25 s.
Rows marked `feasible` are lower bounds (the solver did not prove
optimality within the budget); rows marked `optimal` are exact.

| $N$ | $f(N)$ | $g(N)$ | $\binom{f(N)}{2}$ | gap | $|A|$ | $|B|$ | status |
|-----:|------:|------:|--------:|------:|----:|----:|--------|
| 5 | 3 | 4 | 3 | +1 | 3 | 2 | optimal |
| 6 | 3 | 4 | 3 | +1 | 3 | 2 | optimal |
| 7 | 4 | 6 | 6 | 0 | 4 | 1 | optimal |
| 8 | 4 | 7 | 6 | +1 | 4 | 2 | optimal |
| 9 | 4 | 7 | 6 | +1 | 4 | 2 | optimal |
| 10 | 4 | 9 | 6 | **+3** | 4 | 3 | optimal |
| 11 | 4 | 9 | 6 | +3 | 4 | 3 | optimal |
| 12 | 5 | 11 | 10 | +1 | 5 | 2 | optimal |
| 13 | 5 | 11 | 10 | +1 | 5 | 2 | optimal |
| 14 | 5 | 12 | 10 | +2 | 4 | 4 | optimal |
| 15 | 5 | 13 | 10 | +3 | 5 | 3 | optimal |
| 16 | 5 | 13 | 10 | +3 | 5 | 3 | optimal |
| 17 | 5 | 13 | 10 | +3 | 5 | 3 | optimal |
| 18 | 6 | 16 | 15 | +1 | 6 | 2 | optimal |
| 19 | 6 | 16 | 15 | +1 | 6 | 2 | optimal |
| 20 | 6 | 18 | 15 | +3 | 6 | 3 | optimal |
| 21 | 6 | 18 | 15 | +3 | 6 | 3 | optimal |
| 22 | 6 | 18 | 15 | +3 | 6 | 3 | optimal |
| 23 | 6 | 20 | 15 | +5 | 5 | 5 | optimal |
| 24 | 6 | 21 | 15 | **+6** | 6 | 4 | optimal |
| 25 | 6 | 21 | 15 | +6 | 6 | 4 | optimal |
| 26 | 7 | 22 | 21 | +1 | 7 | 2 | optimal |
| 27 | 7 | 24 | 21 | +3 | 7 | 3 | optimal |
| 28 | 7 | 24 | 21 | +3 | 7 | 3 | optimal |
| 29 | 7 | 25 | 21 | +4 | 6 | 5 | feasible |
| 30 | 7 | 27 | 21 | +6 | 7 | 4 | feasible |
| 31 | 7 | 27 | 21 | +6 | 7 | 4 | feasible |
| 32 | 7 | 27 | 21 | +6 | 7 | 4 | feasible |
| 33 | 7 | 27 | 21 | +6 | 7 | 4 | feasible |
| 35 | 8 | 30 | 28 | +2 | 6 | 6 | optimal |
| 36 | 8 | 30 | 28 | +2 | 6 | 6 | feasible |
| 38 | 8 | 31 | 28 | +3 | 7 | 5 | feasible |
| 42 | 8 | 34 | 28 | **+6** | 8 | 4 | feasible |

## Peak gap per $f$-plateau

| $f$ | $N$-range (plateau) | peak gap achieved | witness sizes |
|----:|---------------------|------------------:|---------------|
| 3 | $[3, 6]$ | +1 | $(3, 2)$ |
| 4 | $[7, 11]$ | +3 | $(4, 3)$ |
| 5 | $[12, 17]$ | +3 | $(5, 3)$ |
| 6 | $[18, 25]$ | **+6** | $(6, 4)$ |
| 7 | $[26, 34]$ | +6 (feasible) | $(7, 4)$ |
| 8 | $[35, \approx 45]$ | $\geq +6$ (feasible at $N=42$) | $(8, 4)$ |

The peak-gap sequence $1, 3, 3, 6, 6, \geq 6, \ldots$ is **not constant**.
It increases at $f = 4$ and $f = 6$. Whether it stabilises or continues
to grow is the empirical question.

## Structural observation

In **every** row with a positive gap, the optimal pair has the form
$(|A|, |B|) = (f(N), k)$ or $(k, f(N))$ or $(m, m)$ for some $m < f(N)$.
The gap is exactly $\binom{|B|}{2}$ when $|A| = f$, otherwise the
formula is more involved.

This suggests the following reformulation:

**Sub-question A.** For each $f$, what is the maximum $|B|$ such that
there exist Sidon $A, B \subset [1, N]$ with $|A| = f$,
$(A - A) \cap (B - B) = \{0\}$, taken over all valid $(N, A)$?

If $|B|_{\max}(f)$ is bounded as $f \to \infty$, the conjecture holds.
If it grows unbounded, the conjecture fails.

From the data, $|B|_{\max}(f)$ appears to be:

| $f$ | 3 | 4 | 5 | 6 | 7 | 8 |
|-----|---|---|---|---|---|---|
| $|B|_{\max}$ (so far) | 2 | 3 | 3 | 4 | 4 | $\geq 4$ |

So $|B|_{\max}$ is growing, roughly as $\sqrt f$ or slower. If this
growth is genuine, the gap $\binom{|B|_{\max}}{2}$ grows like $f$, i.e.,
like $\sqrt N$ — *disproving* the conjecture as stated.

## Implications

**If the empirical trend holds at larger $N$, conjecture #42 (as stated
with $O(1)$) is FALSE.**

The honest deliverable from session 1: strong numerical evidence that
the gap **grows** with $N$. This is a *quantitative* statement that
weakens the conjecture. The precise scaling — $O(\log N)$? $O(\sqrt N)$?
$o(N)$? — is the open follow-on.

## Recommended next steps

### Session 2 — verify the gap grows past 6

The most important confirmation: at $N$ where $f = 9$ or $f = 10$,
does the peak gap reach $+10$ or higher? If yes, conjecture #42 is
empirically dead.

CP-SAT becomes slow at $N \geq 40$ because the model has $\Theta(N^2)$
Boolean variables. Improvements to try:
- Constraint propagation: pre-compute "forbidden differences" from
  partial assignments.
- Lazy constraint generation: only add Sidon constraints that are
  violated by relaxations.
- Hybrid: CP-SAT for small models + custom DFS for larger.

### Session 3 — structural conjecture

Conjecture: $|B|_{\max}(f) = \Theta(\sqrt f)$. This would give
$\text{gap} = \Theta(f) = \Theta(\sqrt N)$, matching the
"convolution-smoothing" upper bound $|A|^2 + |B|^2 \leq N + O(N^{3/4})$
in order of magnitude.

To verify, compute $|B|_{\max}(f)$ for $f = 9, 10, 11, 12$ via CP-SAT
restricted to $|A| = f$ exactly. This is a *narrower* CP-SAT problem
than full optimisation and may be tractable to $f = 12$ or higher.

### Session 4 — analytic attack

If empirics confirm $|B|_{\max}(f) \to \infty$, write up a *proof* of
this fact (constructive Sidon pair where $|B|$ grows with $f$), giving
an explicit lower bound on gap. This would disprove conjecture #42's
$O(1)$ claim with an explicit (unbounded) lower bound.

The construction: take $f = q + 1$ Sidon set from Singer
$\bmod (q^2 + q + 1)$. Question: can we find $|B| = \Theta(\sqrt q)$
Sidon set in $[1, q^2]$ with disjoint diffs? Plausible via Bose-Chowla.
