# Phase 2A — sharper Sidon density for PDS

## Question

Lindström: any Sidon set $A \subset [1, M]$ has $|A| \leq \sqrt M + O(M^{1/4})$.
Cilleruelo–Nathanson [CiNa08, Thm 3]: there exists a PDS with
$\limsup k(x)/\sqrt x \geq 1/\sqrt 2 \approx 0.707$.

**Phase 2A target:** prove $\limsup k(x)/\sqrt x \leq 1 - \delta$ for
some explicit $\delta > 0$ and every infinite PDS $A$. Ideally tight at
$1/\sqrt 2$, matching CiNa08.

## What is automatic

The infinitely-often lower bound $a_n \gg n^{2-o(1)}$ (Phase 2C
Theorem 2) immediately gives:

> **Proposition.** For any infinite PDS and every $c < 2$,
> $\liminf k(x)/x^{1/(2c)} \leq \sqrt 2$. In particular
> $\liminf k(x)/\sqrt x = 0$, and more sharply $k(x) \ll x^{1/4+\varepsilon}$
> at infinitely many $x$.

So we automatically get density that *drops* to $x^{1/4+}$ at sparse $x$.
The question is whether density can also stay near $\sqrt x$ at *other*
$x$.

## Three attempts that fail

`proofs/phase2a_density.tex` writes up three structural attempts:

1. **Cauchy–Schwarz via the partition identity.** Hoped that the PDS
   coverage $T_M = \binom{k(M)}{2}$ ("perfectly packed") forces
   structure. **Failed:** $a_n$ is not monotone, so the covered prefix
   $T_M$ can be much smaller than $\binom{k}{2}$ (e.g. greedy has
   $T_M = 1898$ vs $\binom{2131}{2} = 2.27 \times 10^6$).

2. **Fejér-weighted Plancherel.** For PDS,
   $\int K_T |\widehat{1_A}|^2 = k + T - 1$ when $T \leq T_M$. But the
   only useful upper bound on this integral comes from $|\widehat 1|^2
   \leq k^2$ pointwise, which gives the trivial Sidon constraint
   $T \leq k^2$. The Fejér kernel does not exploit PDS structure
   beyond Sidon at this moment level.

3. **Higher $L^p$ moments.** $\int |\widehat{1_{A_M}}|^{2p}$ for
   $p \geq 4$ counts solutions to $\sum (a_i - b_i) = n$. For Sidon,
   these are determined by $|A|$ alone (every solution is trivial or
   matches a fixed pattern). PDS adds no further constraint at the
   moment level. **No new bound.**

## Why all three fail (structural reason)

The PDS-vs-Sidon distinction shows up in *which* differences appear at
small scales (every $n \in [1, T_M]$ exactly once), not in aggregate
counting quantities. Cauchy–Schwarz and $L^p$ moment identities are
aggregate quantities. The Phase 2C partition argument is the unique
tool we have that uses "which differences appear", and it caps out at
$c = 2$.

## Empirical check on greedy

$k(x)/\sqrt x$ for greedy at scale $x = $ checkpoint 1898:

| $x$ | $k(x)$ | $k(x)/\sqrt x$ | $k(x)/x^{1/3}$ |
|----:|-------:|---------------:|---------------:|
| 100 | 11 | 1.10 | 2.37 |
| $10^4$ | 60 | 0.60 | 2.78 |
| $10^6$ | 320 | 0.32 | 3.20 |
| $10^8$ | 1663 | 0.17 | 3.58 |
| $2 \times 10^8$ | 2131 | 0.15 | 3.63 |

Greedy's $k(x)/\sqrt x$ decays like $x^{-1/6}$, far from saturating
Sidon. Greedy is *not* a witness for the question — it's a PDS where
the density never approaches $\sqrt x$ at large scales. The relevant
witness is CiNa08's construction, which by design achieves
$k(x)/\sqrt x \geq 1/\sqrt 2$ at sparse $x$.

## Sub-targets that remain

1. **Density-zero exceptional set:** $\{x : k(x) > (1-\delta)\sqrt x\}$
   has density 0 in $\mathbb{N}$.
2. **Close the $0.293$ gap** between $1/\sqrt 2$ (CiNa08 lower) and $1$
   (Lindström upper) for $\limsup k(x)/\sqrt x$ of any PDS.
3. **Positive-density Phase 2C:** strengthen the i.o.\ form of
   $a_n \gg n^{2-o(1)}$ to "$a_n \gg n^c$ holds for a positive density
   of $n$".

None of these are obviously attackable with elementary tools.

## Status

Phase 2A as initially framed is open. We documented three structural
attempts and identified three tractable sub-targets, all of which
remain open. **Phase 2A produced no new theorem.**

The honest deliverable is the negative result: the partition argument
(Phase 2C) appears to be the unique elementary tool, and it is sharp
at $c = 2$. Going past requires either:

- a stronger Sidon density bound at "most" $x$ (probably hard),
- restriction / decoupling estimates specific to PDS (probably hard),
- a non-elementary identity from additive combinatorics literature.

These belong to a Phase 2A+ that's substantially harder than what we
attempted.
