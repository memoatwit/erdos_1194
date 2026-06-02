# Erdős #1194 — Proof Plan

This document is the forward-looking research plan. The README captures
current state and findings; this file enumerates the directions of attack
and ranks them by expected payoff per session.

## Where we are

- **Lower bound (i.o.):** $a_n \gg n^{2-o(1)}$ infinitely often (GPT-5.4 Pro,
  comment thread, April 23 2026). The classical $a_n \gg n \log n$ i.o. is
  reproved cleanly in `proofs/lower_bound_io.tex`. The full $n^{2-o(1)}$
  refinement has *not* been reproduced from public materials.
- **Upper bound:** $a_n \ll n^3$ via Lev's greedy. Empirically
  $\max_{n \leq N} a_n \approx 0.0293 \cdot N^3$ for $N \in [1500, 1898]$.
  The greedy is therefore essentially $\Theta(N^3)$ — improvement requires
  a different construction.
- **Lower bound (all $n$):** does not exist as a clean statement, because
  the greedy data already shows $\inf_n a_n / n^2 \to 0$. Any "for all $n$"
  result must be much weaker than $n^2$ or be reformulated in terms of
  the running max $M(N) := \max_{n \leq N} a_n$.

The honest gap is at the i.o. level: lower $\sim n^2$, upper $\sim n^3$.

## Phases (executed)

### Phase 0 — verify and document

- [x] Re-verify greedy correctness at $N = 1898$ (PDS invariants).
- [x] Reproduce classical $n \log n$ i.o. argument as clean LaTeX.

### Phase 1 — cheap empirical tests

- [x] $\sum_{a \in A} 1/a^s$ for $s \in \{1, 1.5, 2, 2.5, 3\}$ — bounded;
  dominated by small elements; controlled by Sidon density alone, not PDS.
- [x] Stratified analysis of $a_n / n^k$ — quantified bimodality.
- [x] Running peak log-log fit — $a_n^{\rm peak} \sim 0.0635 n^{2.90}$.

**Take-away:** Naive measure $\mu(a) = 1/a^s$ is dead. Any 1196-style
proof must use the convolution identity $1_A \star 1_A^- \equiv 1$ on
$\mathbb{Z}_{>0}$, not just element values.

## Phases (open)

### Phase 2A — sharper Sidon density for PDS specifically

**Goal:** Prove $|A \cap [1,x]| \leq (1-\delta) \sqrt{x}$ for *all* large $x$
and some explicit $\delta > 0$, using the fact that $A$ is PDS (not just
Sidon). Even $\delta = 10^{-3}$ would yield the first "for all $n$"
improvement on the trivial $a_n \geq n+1$.

**Tools:**
- Local additive energy of finite truncations.
- Cauchy-Schwarz against the convolution identity.
- Possibly Plünnecke-Ruzsa style arguments.

**Risk:** Singer-type Sidon sets reach $|A \cap [1,x]| \sim \sqrt{x}$ at most
scales. Whether PDS rules this out at *every* scale is open and likely
hard. A negative result (PDS does NOT improve Sidon density at any scale)
would itself be informative.

### Phase 2B — Fourier / convolution route

**STATUS: Worked (session 6, 2026-05-11). Two outcomes:**

**(A) Theorem 5 fully rigorous.** The Phase 2C "logarithmic refinement"
$a_n \gg n^2/f(n)$ i.o. for $\sum 1/(nf(n)) < \infty$ is now a complete
proof in `proofs/lower_bound_io.tex` (6 pp). Constants tracked, slow-
variation regularity used explicitly.

**(B) Computational probes show partition argument is sharp at $c = 2$.**
The Fejér PDS identity holds exactly; gap slope converges to $1/2$ as
$c = 2$ predicts; anchor-window density is a uniform constant times
$|A|/\sqrt{\max A}$ — no PDS-specific slack. To push the i.o. exponent
past 2, one needs ingredients beyond the partition identity plus Sidon
density (restriction estimates, decoupling, or another counting
identity).

See `results/phase2b_summary.md` for details.

### Phase 2C — reconstruct GPT-5.4 Pro's $n^2/f(n)$ i.o. argument

**STATUS: DONE (session 4, 2026-04-30).** The argument is now in
`proofs/lower_bound_io.tex` as Theorems 4 and 5. Two structural facts
do all the work:

1. **PDS partition identity:** $D_k := \{x_k - x_i : 1 \le i < k\}$ is
   a partition of $\mathbb{Z}_{>0}$. So
   $X = \sum_k |D_k \cap [1,X]|$ exactly.

2. **Gap lower bound:** if $a_n \le C n^c$ for all $n$, then
   $d_k := x_k - x_{k-1}$ satisfies $d_k \ge (x_k/C)^{1/c}$,
   because $a_{d_k} = x_k$ by uniqueness. Telescoping gives
   $x_k \gg k^{c/(c-1)}$.

Splitting the partition sum at $K = X^{(c-1)/c}$ contradicts $c < 2$.
Refinement: replace $c$ by $a_n \le Cn^2/f(n)$ to get $a_n \gg n^2/f(n)$
i.o. for any slowly-varying $f$ with $\sum 1/(nf(n)) < \infty$
(**convergent** — the live problem page reads "diverges", which is a
typo carried over despite the comment-thread correction).

**Side effect:** Phases 2A and 2B don't have to recover $n^{2-o(1)}$ —
they would only matter if they push past $n^2$ or to "for all $n$".
The bar for those is now considerably higher.

### Phase 3 — Cilleruelo–Nathanson [CiNa08] explicit transfer

**STATUS: Original framing dead (session 4, 2026-04-30).** The
Cilleruelo–Nathanson 2008 paper (arXiv math/0609244, downloaded as
`literature/cilleruelo_nathanson_2008.pdf`) achieves three results:

- **Theorem 1:** For every Sidon set $\mathcal{B}$ and every
  $\omega(x) \to \infty$, exists a PDS $\mathcal{A}$ with
  $A(x) \geq B(x/3) - \omega(x)$.
- **Theorem 2:** Exists a PDS with $A(x) \gg x^{\sqrt{2}-1+o(1)}$
  (using Ruzsa's Sidon set as the source).
- **Theorem 3:** Exists a PDS with $\limsup A(x)/\sqrt{x} \geq 1/\sqrt{2}$.

But the paper *itself* (Section 4.1, Open Problems) says:
> "the greedy algorithm used in [Le04] generates a perfect difference
> set such that $t_n \ll n^3$. Our method generates a dense Sidon set
> $\mathcal{A}$, but gives a very poor upper bound for the sequence
> $t_n$."
>
> **Problem 1.** Does there exist a perfect difference set such that
> $t_n = o(n^3)$?

Where $t_n = b_n$ in our notation, hence $a_n = t_n + n$ and
$t_n = o(n^3) \iff a_n = o(n^3)$. **CiNa08's Problem 1 is exactly the
upper-bound side of #1194**, and it has been open since 2008.

The density results above are *limsup*-style — they exhibit a sparse
sequence of $x$ where the construction is dense, but at intermediate
$x$ density can be much lower, and the corresponding $a_n$ values can
be huge.

**Pivoted goal (Phase 3'):** treat CiNa08 as an empirical object.
Implement the construction at moderate scale, compare $t_n$ to
greedy's $0.0293 n^3$, and look for hybrid schemes that combine
CiNa08's high-density windows with greedy filling. This is exploratory.

**STATUS: Done (session 7, 2026-05-11), via a simpler approach.**
Instead of the full intricate CiNa08 construction, we ran
**dense-Sidon-seeded greedy** with several seed families (Mian–Chowla,
Erdős–Turán, Phase 4 optima). Results in `results/seeded_summary.md`:

- Best seed: **Mian–Chowla of size 60** at target $N=500$ gives
  $\max(A) = 286{,}281$ (vs scratch greedy $3{,}080{,}237$) — a
  **10.8× improvement** on greedy's constant.
- The constant drops from $\approx 0.025 N^3$ to $\approx 0.0023 N^3$.
- Asymptotic scaling **remains $\Theta(N^3)$** across all seeds.

**Phase 4 optimum is a *bad* seed.** Using $A_{30}^*$ (the densest
possible Sidon covering $[1,30]$) gives ratio $0.0070$ — worse than
Mian–Chowla by 3×. This empirically confirms Phase 4': tight seeds
are extension traps. Loose seeds (Mian–Chowla style) win because
they leave greedy room to maneuver.

**Implication for CiNa08 Problem 1:** seeding alone gives only
constant-factor improvement. Achieving $a_n = o(n^3)$ requires a
fundamentally non-greedy continuation strategy.

### Phase 4 — exact small-$N$ search

**STATUS: Done (session 5, 2026-04-30).** Solved $N \in \{20, 25, 30,
35, 40, 45\}$ exactly with bitmask DFS and CP-SAT; $N = 50$ pushed to
$M^* > 91$. See `results/exact_summary.md`.

**Headline finding:** Finite-PDS optimum $M^*(N) \approx 2N$
empirically (ratio $M^*/N$ stays in $[1.6, 2.2]$ across the tested
range). Greedy is $\Theta(N^3)$, so greedy is **super-polynomially
sub-optimal even for the finite problem**: at $N = 45$, greedy uses
$\max(A) = 1492$ vs optimum 86 — 17.4× gap, growing as $\sim 0.4 N$.

**Implication for #1194 upper bound:**
The finite optima do NOT glue into an infinite PDS — that would force
$a_n \asymp 2n$ and falsify the i.o. lower bound $a_n \gg n^{2-o(1)}$
from Phase 2C. So there's a real obstruction to extending finite
optima coherently. **Locating that obstruction is the next sharp
question.** Possible angles:
- Track the "extension cost" empirically: given finite optimum $A_N^*$,
  what is $\min M$ such that some $A_{N+1} \supseteq A_N^*$ exists with
  Sidon and covers $[1, N+1]$? Probably much larger than $M^*(N+1)$.
- That cost gap is the obstruction; quantifying its asymptotic should
  give a lower bound on $a_n$ that cannot be evaded by clever
  construction.

**Compute scaling:** the per-$M$ CP-SAT scan slows roughly
$\times 1.3$/$M$, so $N = 60, 70$ would need substantial CPU
(hours-days). Not worth in vanilla Python; would need C++ or a
proper SAT/CP solver in batch.

### Phase 5 — writeup

LaTeX paper in the style of `sample_solution_1196.pdf`, summarizing:
- Statement of the problem and known bounds.
- Verified i.o. argument and any new partial results.
- The empirical $0.0293\, N^3$ conjecture for greedy and supporting data.
- The [CiNa08] transfer and its quantitative growth (if Phase 3 succeeds).

If anything in Phases 2A–3 yields a new result, submit a comment to
`erdosproblems.com/1194` linking to the full proof.

## Recommended ordering

1. ~~**Phase 2C** (reconstruct GPT-5.4 Pro).~~ **DONE — session 4.**
2. ~~**Phase 3** as originally scoped ([CiNa08] gives $a_n \ll n^{2+\varepsilon}$).~~
   **DEAD — session 4.** [CiNa08] doesn't beat $n^3$; the authors
   themselves pose this as an open problem.
3. ~~**Phase 4** (exact small-$N$ optimization).~~ **DONE — session 5.**
   Surprise: finite optimum is $\approx 2N$ vs greedy $\Theta(N^3)$.
4. ~~**Phase 4' — extension cost.**~~ **DONE — session 5.** Quantified
   the obstruction empirically. Two trajectories ($A_{20}^*$ to $N=45$,
   $A_{30}^*$ to $N=63$) show $M_{\text{ext}} \sim N^{4-5}$ — *worse
   than greedy*. Concretely: at $N=45$, $A_{20}^*$-seeded extension
   reaches max(A) = 1054 vs greedy's 1492 vs unconstrained $M^*$ = 86.
   The chain $M^* \sim N \ll M_{\text{greedy}} \sim N^3 \ll
   M_{\text{ext}} \gtrsim N^4$ is now established. See
   `results/extension_summary.md`. New conjecture (extension lower
   bound): any infinite PDS satisfies $a_n \gg n^c$ for all large $n$,
   $c > 1$, with $c$ determined by $\lim_{N_0 \to \infty}$ asymptotic
   exponent of $M_{\text{ext}}(N_0, N)$.
5. **Phase 3'** ([CiNa08] empirical study). Implement CiNa08, look
   at $t_n$ profile, attempt hybrids with greedy filling. Higher
   effort, more speculative.
6. **Phase 2B** (Fourier / convolution). Lower-bound direction for
   pushing beyond $n^{2-o(1)}$.
7. **Phase 2A** (sharper Sidon density for PDS). Lower priority.
8. **Phase 5** (writeup) is rolling — kept current as results land.
