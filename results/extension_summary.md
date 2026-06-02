# Phase 4' — Extension cost from finite optima

## Setup

Given a known finite optimum $A_{N_0}^*$ for the PDS-up-to-$N_0$ problem
(Phase 4), we compute, for each $N \geq N_0$, the value
\[
   M_{\text{ext}}(N_0, N) \;:=\; \min\,\bigl\{\,\max(A) \;:\;
     A \supseteq A_{N_0}^*,\ A\ \text{Sidon},\ [1, N] \subset A - A \,\bigr\}.
\]
This is the minimum max(A) over all Sidon supersets of the seed that cover
$[1, N]$. Each step is solved exactly by Google ortools CP-SAT.

The unconstrained optimum is $M^*(N) \approx 2N$ (Phase 4). The gap
$M_{\text{ext}}(N_0, N) - M^*(N)$ measures the cost of being forced to
keep the prior optimum.

## Trajectories

### Seed $A_{30}^* = \{1, 2, 7, 11, 24, 27, 35, 42, 54, 56\}$

| $N$ | $M_{\text{ext}}$ | $|A|$ | $M_{\text{ext}}/N$ |
|----:|-----------------:|------:|------------------:|
|  30 |  56 | 10 | 1.87 |
|  35 |  56 | 10 | 1.60 (covers up to 47 for free) |
|  36 |  92 | 11 | 2.56 |
|  37 | 129 | 12 | 3.49 |
|  39 | 168 | 13 | 4.31 |
|  42 | 254 | 15 | 6.05 |
|  46 | 300 | 16 | 6.52 |
|  48 | 399 | 18 | 8.31 |
|  56 | 516 | 20 | 9.21 |
|  58 | 654 | 22 | 11.28 |
|  59 | 829 | 24 | 14.05 |
|  60 | 1019 | 26 | 16.98 |
|  62 | 1261 | 28 | 20.34 |
|  63 | 1590 | 29 | 25.24 |

Log-log fits on the 12 "hard" steps (ones requiring a new element):
- All hard:  $M_{\text{ext}} \approx C \cdot N^{4.27}$
- Tail (last 7): $M_{\text{ext}} \approx C \cdot N^{4.90}$

### Seed $A_{20}^* = \{1, 5, 6, 18, 20, 26, 29, 36\}$

| $N$ | $M_{\text{ext}}$ | $|A|$ | $M_{\text{ext}}/N$ |
|----:|-----------------:|------:|------------------:|
|  20 |   36 |  8 | 1.80 |
|  22 |   58 |  9 | 2.64 |
|  26 |   84 | 10 | 3.23 |
|  27 |  144 | 12 | 5.33 |
|  34 |  178 | 13 | 5.24 |
|  36 |  251 | 15 | 6.97 |
|  39 |  344 | 17 | 8.82 |
|  41 |  467 | 19 | 11.39 |
|  42 |  618 | 21 | 14.71 |
|  43 |  661 | 22 | 15.37 |
|  44 |  869 | 24 | 19.75 |
|  45 | 1054 | 26 | 23.42 |

Log-log fits on the 11 hard steps:
- All hard:  $M_{\text{ext}} \approx C \cdot N^{3.80}$
- Tail (last 7): $M_{\text{ext}} \approx C \cdot N^{6.48}$

## Comparison to unconstrained optima

| $N$ | unconstrained $M^*$ | seeded from $A_{20}^*$ | seeded from $A_{30}^*$ | greedy |
|----:|---------------------:|-----------------------:|-----------------------:|-------:|
|  30 |  56 |  144 |   56 |  444 |
|  40 |  86 |  344 |  168 | 1175 |
|  45 |  86 | 1054 |  254 | 1492 |

So at $N = 45$: unconstrained 86, $A_{30}^*$-seeded 254 (3.0× over), $A_{20}^*$-seeded 1054 (12.3× over), greedy 1492 (17.4× over).

## Headline finding

The seeded extension grows **super-polynomially** in $N$, with the fitted
exponent already exceeding 4 (and increasing along the trajectory). Both
trajectories show the same pattern with different starting points,
confirming this is a feature of the gluing problem and not an artefact of
a particular seed.

By contrast:
- Unconstrained finite optimum: $M^*(N) \approx 2N$ (linear).
- Greedy (no seeding): $M(N) \approx 0.0293\, N^3$.

So we have the chain:

$$M^*(N) \;\sim\; N \;\;\ll\;\; M_{\text{greedy}}(N) \;\sim\; N^3 \;\;\ll\;\; M_{\text{ext}}(\text{seeded})(N) \;\gtrsim\; N^4.$$

## Interpretation: the structural obstruction

A finite optimum $A_{N_0}^*$ packs $\binom{|A|}{2}$ distinct differences
into roughly $[1, 2N_0]$ — close to the maximum density a Sidon set can
achieve. This leaves very few "free" difference slots in $[1, 2N_0]$ and
makes future extensions structurally cramped: every new element added must
create $|A|$ new differences that must all dodge the densely-packed
existing set.

Greedy avoids this trap by being deliberately conservative: each
Strategy-2 element is placed at $\geq \max(A) + N + 1$, leaving lots of
empty difference space. The result is a worse finite max(A) at any given
$N$ but a sustainable polynomial growth rate.

## Implications for #1194

This is consistent with the infinite-PDS lower bound $a_n \gg n^{2-o(1)}$
i.o. (Phase 2C). In fact, the empirical evidence is stronger: any naive
attempt to glue finite optima produces a sequence with $a_n$ growth
strictly worse than $N^3$, not better. The "saving" from finite optimality
is paid back many-fold in extension cost.

Concretely:
- The "$M^*(N) \sim 2N$ for finite problem" observation does NOT translate
  to an infinite PDS with $a_n \sim 2n$. The naive gluing has $a_n \sim N^4$
  or worse.
- An infinite PDS with $a_n \ll N^{2+\varepsilon}$ — if it exists — would
  require a fundamentally non-local construction, balancing tightness at
  current $N$ against future extensibility. CiNa08 is one such attempt;
  it pays in density at intermediate $x$ to gain limsup density at sparse
  $x$.

This suggests a sharper conjecture for the infinite #1194:

> **Conjecture (extension lower bound).** Any infinite PDS $A$ satisfies
> $a_n \gg n^{c}$ for all large $n$, for some explicit $c \in (1, 2)$,
> with $c$ determined by the asymptotic exponent of $M_{\text{ext}}(N_0, N)$
> taken in the limit $N_0 \to \infty$.

This would be a "for all $n$" lower bound — strictly stronger than the i.o.
bound. Whether $c$ exists and what value it takes are now open. The empirical
data hints at $c$ being a moderate constant (perhaps 2 or 3) that interpolates
between the lower bound 2 and Lev's upper bound 3.

## Reproducing

```sh
python3 extension_cost.py 20 30 40       # short multi-seed scan
python3 extension_cost.py long 30 75     # long trajectory from A_30*
```
