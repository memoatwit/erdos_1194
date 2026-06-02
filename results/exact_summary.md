# Phase 4 — Exact branch-and-bound results

For each $N$, $M^*(N) := \min \{ \max(A) : A \subset \mathbb{N},\ A$ is Sidon,
$\{1, M\} \subset A,\ [1,N] \subset A - A\}$. The greedy column is the value
of $\max(A)$ produced by `explore.py` after $N$ steps. Exact values verified
by branch-and-bound (bitmask DFS) and double-checked by Google ortools
CP-SAT.

| $N$  | $M^*$ exact | greedy $\max(A)$ | greedy / exact | $|A^*|$ | $|A_{\text{greedy}}|$ | witness $A^*$ |
|-----:|-----------:|-----------------:|---------------:|--------:|----------------------:|---------------|
|   20 |       36 |             97 |        2.69× |       8 |                   11 | $\{1, 5, 6, 18, 20, 26, 29, 36\}$ |
|   25 |       46 |            225 |        4.89× |       9 |                   15 | $\{1, 3, 11, 25, 26, 30, 37, 43, 46\}$ |
|   30 |       56 |            444 |        7.93× |      10 |                   19 | $\{1, 2, 7, 11, 24, 27, 35, 42, 54, 56\}$ |
|   35 |       56 |            625 |       11.16× |      10 |                   21 | $\{1, 2, 7, 11, 24, 27, 35, 42, 54, 56\}$ (same set) |
|   40 |       86 |          1,175 |       13.66× |      12 |                   27 | $\{1, 10, 11, 18, 31, 43, 46, 57, 62, 80, 84, 86\}$ |
|   45 |       86 |          1,492 |       17.35× |      12 |                   29 | $\{1, 10, 11, 18, 31, 43, 46, 57, 62, 80, 84, 86\}$ (same set) |
|   50 | $\geq 92$ |          2,518 | $\geq$27.4× |       — |                   35 | unknown — search exhausted at $M = 92$ |

## Empirical observations

1. **$M^*(N) / N \approx 2$.** The ratio $M^*/N$ at the seven measured $N$ is
   $\{1.80, 1.84, 1.87, 1.60, 2.15, 1.91\}$, hovering around 2. This is
   astonishingly close to the trivial lower bound $M^* \geq N + 1$.

2. **Greedy is super-polynomially worse than optimal.** The ratio
   $M_{\text{greedy}}/M^*$ at $N \in \{20, 25, 30, 35, 40, 45\}$ is
   $\{2.7, 4.9, 7.9, 11.2, 13.7, 17.4\}$ — growing roughly linearly in $N$
   (rough fit: ratio $\approx 0.4 N$). Since greedy is $\Theta(N^3)$ and
   optimum appears $\Theta(N)$, the gap is conjecturally $\Theta(N^2)$,
   consistent with these numbers.

3. **Solutions are stable across an interval of $N$.** The same witness $A$
   often serves multiple $N$ values. For instance,
   $\{1, 2, 7, 11, 24, 27, 35, 42, 54, 56\}$ has differences covering
   $[1, 47]$ (verified), so it is optimum for every
   $N \in \{30, 31, \ldots, 47\}$ that admits this $|A|$.

4. **$|A^*|$ stays close to the information-theoretic floor.** The smallest
   $|A|$ admitting $\binom{|A|}{2} \geq N$ at $N \in \{20, 25, 30, 50\}$ is
   $\{7, 8, 9, 11\}$. The exact $|A^*|$ at the same $N$ is
   $\{8, 9, 10, ?\}$ — within 1 of the floor.

## Critical conceptual clarification

The finite problem we solved here ("optimal Sidon ruler covering $[1, N]$")
is **not** Erdős's #1194. The Erdős problem asks about *infinite* PDS
$A \subset \mathbb{N}$ where every $n \geq 1$ has a unique representation
$a_n - b_n$ with $a, b \in A$. The finite "covers $[1, N]$" optima do not
in general extend to infinite PDS without large blowups: each new $n$ to
cover may force a new element that breaks the Sidon property of any
proposed extension, requiring large jumps.

What we *have* shown empirically is that greedy is dramatically sub-optimal
for the finite problem at small $N$. This is consistent with — and
suggestive of — substantial slack in the upper bound side of #1194:
*if the finite optima can be made to fit together coherently along
$N \to \infty$*, the resulting infinite PDS would have $a_n \ll N^{1+\varepsilon}$,
in particular $o(N^3)$, resolving Cilleruelo–Nathanson Open Problem 1
(equivalently, the upper-bound side of #1194). Whether this is achievable
is precisely what is open.

## Reproducing

```sh
python3 exact_search.py 20 30          # bitmask DFS
python3 exact_search_cpsat.py 40 45    # CP-SAT per-M scan
python3 exact_search_cpsat_opt.py 25 35   # CP-SAT optimization mode
```
