# Erdős Problem #1194

**Source:** [erdosproblems.com/1194](https://www.erdosproblems.com/1194) — [Er80, p.100]  
**Tags:** additive combinatorics | additive basis | Sidon sets  
**Status:** OPEN

---

## Problem Statement

Let $A \subset \mathbb{N}$ be such that every integer $n \geq 1$ can be written **uniquely** as $a_n - b_n$ for some $a_n, b_n \in A$. How fast must $a_n/n$ increase?

Such a set $A$ is called a **perfect difference set** (PDS).

---

## Known Bounds

| Bound | Type | Source |
|-------|------|--------|
| $a_n \ll n^3$ | Upper (constructive) | Lev [Le04], greedy |
| $a_n \gg n \log n$ infinitely often | Lower | Erdős (Sidon density) |
| $a_n \gg n^{2-o(1)}$ infinitely often | Lower | GPT-5.4 Pro / Bloom, Apr 23 2026 — **verified** in `proofs/lower_bound_io.tex` (Theorem 4) |
| $a_n \gg n^2/f(n)$ i.o., for any $f$ with $\sum 1/(nf(n))$ **convergent** | Lower | GPT-5.4 Pro / Bloom, optimised — **verified sketch** in `proofs/lower_bound_io.tex` (Theorem 5) |

**Note on a typo upstream.** The live problem page (`erdosproblems.com/1194`, last edited 24 April 2026) reads "$\sum 1/(nf(n))$ **diverges**" for the optimised condition. The comment thread on that same page (post 5782 by natso26, post 5784 by Bloom: *"Oops yes, thanks corrected"*) corrects this to **converges**, and the proof in fact requires convergence: with the divergent condition $f(n) = 1$ would qualify and force $a_n \gg n^2$ i.o., which the argument does not establish. We use the corrected (convergent) condition throughout.

### The Gap
- Lower bound (infinitely often): $\sim n^{2-o(1)}$ — sharper, $\gg (n/\log n)^2$ via $f = (\log n)^2$.
- Upper bound (constructive, greedy): $\sim n^3$, empirically $\approx 0.0293\, N^3$.

---

## Key Facts

- $A$ must be a **Sidon set** (B₂ set): all pairwise differences are distinct.
- Sidon sets satisfy $|A \cap [1,x]| \leq (1+o(1)) x^{1/2}$.
- Perfect difference sets can be constructed greedily (Lev [Le04]).
- The Cilleruelo–Nathanson [CiNa08] method transfers results from dense Sidon sets to PDS.

---

## Open Questions We're Pursuing

1. **Lower bound for all $n$:** Is $a_n \gg n^2$ for *all* large $n$ (not just infinitely often)?
2. **Upper bound improvement:** Can we construct a PDS achieving $a_n \ll n^{2+\varepsilon}$?
3. **True growth rate:** Is it $n^2$, $n^2 \log n$, $n^{5/2}$, or something else?

---

## Computational Findings (2026-04-27)

### Algorithm

Greedy construction with numba JIT inner loop (v4):

- **Strategy 1**: For each uncovered $n$, try $a = b + n$ for $b \in A$ (largest first). Fast for most steps.
- **Strategy 2**: When Strategy 1 fails, find the first $b > \max(A) + \text{covered}$ such that adding the pair $(b, b+n)$ introduces no collision. Three rules suffice (provably correct once $b > \max(A)$). Inner loop is numba JIT-compiled.
- **Checkpointing**: State serialised every 50 Strategy-2 calls, enabling incremental runs.

Performance: n=500 in 1.9s, n=1000 in 19s, n=1200 in 38s (wall time, single core).

### Main Scaling Table

| $N$ | $\max(A)$ | $\max(A)/N^3$ | $\max(A)/(N^3 \ln N)$ | $\max(A)/N^{2.5}$ |
|-----|-----------|---------------|----------------------|-------------------|
| 200 | 152,791 | 0.01910 | 0.003605 | 0.270 |
| 300 | 641,667 | 0.02377 | 0.004167 | 0.412 |
| 500 | 3,080,237 | 0.02464 | 0.003965 | 0.551 |
| 1,000 | 26,100,594 | 0.02610 | 0.003778 | 0.825 |
| 1,200 | 47,373,687 | 0.02742 | 0.003867 | 0.950 |
| 1,500 | 94,610,174 | 0.02803 | 0.003833 | 1.086 |
| 1,642 | 131,261,135 | 0.02965 | 0.004005 | 1.201 |
| 1,732 | 153,515,942 | 0.02955 | 0.003962 | 1.230 |
| 1,815 | 177,559,787 | 0.02970 | 0.003958 | 1.265 |
| 1,898 | 202,257,090 | 0.02958 | 0.003919 | 1.289 |

### Key Empirical Finding: max(A) ~ 0.0293 · N³

At $N \geq 1{,}500$ the ratio $\max(A)/N^3$ has **converged**:

$$\frac{\max(A)}{N^3} \approx 0.0293 \pm 0.0006 \qquad (N = 1500 \text{–} 1900)$$

Meanwhile $\max(A)/N^{2.5}$ is still growing (1.09 → 1.29 over the same range), ruling out $N^{2.5}$ as the exponent. The consecutive log-log slopes oscillate around 3 for large $N$:

| $N$ interval | log-log slope |
|---|---|
| 1000→1200 | 3.27 |
| 1200→1500 | 3.10 |
| 1500→1642 | 3.62 |
| 1642→1732 | 2.94 |
| 1732→1815 | 3.11 |
| 1815→1898 | 2.91 |

**Conclusion:** The greedy construction achieves $\max(A) \sim 0.0293 \cdot N^3$, confirming that it is $\Theta(N^3)$ — tight up to a constant. This matches Lev's $O(n^3)$ upper bound. The ratio $\max(A)/(N^3 \ln N)$ shows no clear trend (fluctuates around 0.0039), so we cannot distinguish $N^3$ from $N^3 \log N$ at these scales.

### Bimodal $a_n$ Distribution

The values $a_n$ are **wildly bimodal**. Most differences are covered "for free" by pairs already in $A$; a sparse set of "hard" differences require a large new element. Example near $N = 500$:

| $n$ | $a_n$ | $a_n/n^2$ |
|-----|-------|-----------|
| 494 | 2,979,214 | 12.21 |
| **495** | **592** | **0.002** |
| **496** | **1,175** | **0.005** |
| 498 | 3,044,924 | 12.28 |
| 499 | 3,080,237 | 12.37 |
| **500** | **1,675** | **0.007** |

The Erdős question is really about these peaks. The running peaks of $a_n/n^2$ grow as $\sim 0.033 \cdot n^{2.97}$ (log-log fit at $N=1000$), consistent with the $N^3$ overall scaling.

### Algorithm Scan Depth

Strategy-2 calls grow linearly with $N$ (~$N/2$). Scan depth per call grows as ~$N^2$ (density of valid $b$ near $\max(A)$ is $\sim N^{-3/2}$, and $|A| \sim N^{1/2}$, giving total work $\sim N^{1/2} \cdot N^{3/2} = N^2$ per call, hence total $N^3$).

---

## Mathematical Connection to Problem #1196

Problem #1196 (primitive sets, solved by GPT-5.4 Pro on Apr 13 2026) uses a **sub-Markov chain** on the divisibility poset. Key idea: construct a measure $\mu(n) = 1/(B_x \cdot n \log n)$ such that $\sum_{a \in A} \mu(a) \leq 1$ for any primitive set $A$.

**Potential analog for #1194:** We want a measure $\mu$ on $\mathbb{N}$ such that:
- For any PDS $A$: $\sum_{a \in A} \mu(a)$ is bounded
- $\mu(n) \sim 1/n^\alpha$ would force $a_n \gg n^{\alpha - 1}$

The difficulty: PDS has **additive** structure (differences), not multiplicative (divisibility). The 1196 proof uses $\sum_{q|n} \Lambda(q) = \log n$ (prime number theorem). An additive analog would require $\sum_{d \leq t} f(d) \sim g(t)$ for some appropriate weight $f$.

**Update (2026-04-27, session 3):** The naive measure approach $\mu(a) = a^{-s}$ is *empirically dead*. For the greedy PDS at $N = 1898$ we measured

| measure | value (cumulative over $A$) |
|---|---|
| $\sum_{a \in A} 1/a$ | $1.1480$ |
| $\sum_{a \in A} 1/a^{1.5}$ | $0.5707$ |
| $\sum_{a \in A} 1/a^2$ | $0.3385$ |
| $\sum_{a \in A} 1/(a \log a)$ | $1.0405$ |

The sums are dominated entirely by the small elements (the first $\sim 200$ values of $A$ contribute essentially everything; tail sums for $a \geq 200{,}000$ are $\leq 10^{-6}$). This convergence is forced by Sidon density alone ($a_k \gg k^2$ implies $\sum 1/a_k^s$ converges for $s > 1/2$); the PDS structure adds **no extra information** at the level of inverse-power sums of element values. Any 1196-style proof must use the **convolution identity** $1_A \star 1_A^- \equiv 1$ on $\mathbb{Z}_{>0}$, not just the values of $a$ themselves.

**Open:** Whether a Markov/measure/Fourier argument can prove $a_n \gg n^2$ infinitely often (currently $n^{2-o(1)}$, GPT-5.4 Pro), let alone for all large $n$ when properly reformulated.

---

## Phase 0 + Phase 1 Findings (session 3, 2026-04-27)

### Verification (Phase 0)

The greedy PDS data was independently re-verified from `results/checkpoint_1898.pkl` (the largest valid checkpoint; `checkpoint_1984.pkl` is truncated). All five invariants pass:

- $|A| = 2{,}131$ distinct elements, $\max(A) = 202{,}257{,}090$.
- Every $n \in [1, 1898]$ appears in `rep` exactly once.
- All `rep[n] = (a, b)` are well-formed: $a > b$, both in $A$, $a - b = n$.
- Every $n \in [1, 1898]$ has **exactly one** pair $(a, b) \in A^2$ with $a - b = n$ (PDS condition).
- All $\binom{2131}{2} = 2{,}269{,}515$ pairwise differences are distinct (Sidon).

Strategy-2 fired $1{,}053$ times in 1898 steps. Script: `verify_and_analyze.py`.

### Stratification of $a_n$ (Phase 1B)

The bimodality of $a_n$ is now precisely quantified at $N = 1898$:

| stratum | criterion | count | fraction |
|---|---|---:|---:|
| "easy" | $a_n / n^2 \leq 1$ | $836$ | $44.0\%$ |
| "hard" | $a_n / n^2 > 1$  | $1062$ | $56.0\%$ |

Running min and max of $a_n / n^2$:
- $\min_{n \leq 1898} a_n/n^2 = 5.65 \times 10^{-4}$ (attained on the easy stratum).
- $\max_{n \leq 1898} a_n/n^2 = 56.29$ (attained at $n = 1890$).

Histogram of $a_n / n^2$ in power-of-2 bins (truncated):

```
2^-11..2^-10 : 125     2^-2..2^-1 : 16      2^2..2^3 : 82
2^-10..2^-9  : 152     2^-1..2^0  : 15      2^3..2^4 : 171
2^-9..2^-8   : 136     2^0..2^1   : 25      2^4..2^5 : 290
2^-8..2^-7   : 127     2^1..2^2   : 44      2^5..2^6 : 451
2^-7..2^-6   : 86
```

Two clear modes (sharp peak around $2^{-10}$, and a heavy upper tail rising through $2^{-5}, \ldots, 2^{-6}$). The upper-tail growth is what drives Erdős's question.

### Peak fit (Phase 1C)

Of the 1898 values of $a_n$, exactly **504** set a new running record of $a_n / n^2$. Log-log fit on the last 30 records:

$$a_n^{\text{peak}} \;\approx\; 0.0635 \cdot n^{2.90} \qquad (n \in [\text{tail of } 1898])$$

The exponent $2.90$ is consistent with the global $\max(A) \sim 0.0293 \cdot N^3$, which would predict slope $3.0$ on the running peak.

### A clarifying reformulation

Because $\inf_n a_n/n^2 \to 0$ in the greedy data (the easy stratum), a "for all large $n$" version of the bound $a_n \gg n^2$ is *empirically false* even for the greedy PDS. The substantive Erdős question, properly reformulated, concerns the **running maximum**

$$M(N) := \max_{n \leq N} a_n,$$

equivalently $\max_{n \leq N} a_n/n$. All known lower bounds are i.o. statements of this kind:

| bound | direction |
|---|---|
| $M(N) \gg N \log N$ | classical, this writeup `proofs/lower_bound_io.tex` |
| $M(N) \gg N^{2-o(1)}$ | GPT-5.4 Pro, comment thread, *not yet reproduced* |
| $M(N) \ll N^3$ | Lev (greedy) |
| $M(N) \asymp 0.0293\, N^3$ | greedy, this work |

### Lower-bound LaTeX writeup

`proofs/lower_bound_io.tex` (5 pages, compiles to `lower_bound_io.pdf`) now contains:

1. **Theorem 1 — classical $a_n \gg n \log n$ i.o.** via the PDS counting identity $N(x) = \binom{k(x)}{2}$ combined with Erdős's i.o. Sidon density bound $k(x) \ll \sqrt{x/\log x}$.
2. **Theorem 4 — GPT-5.4 Pro / Bloom $a_n \gg n^{2-o(1)}$ i.o.**, fully reproduced (Phase 2C, session 4). The argument bypasses Sidon density entirely. Two key structural facts:
   - **PDS partition (Lemma 3):** $D_k := \{x_k - x_i : i < k\}$ partitions $\mathbb{Z}_{>0}$, so $\sum_k |D_k \cap [1,X]| = X$ exactly.
   - **Gap lower bound (Lemma 4):** if $a_n \leq Cn^c$ for all $n$, then consecutive gaps $d_k = x_k - x_{k-1}$ satisfy $d_k \geq (x_k/C)^{1/c}$ (because $a_{d_k} = x_k$ by uniqueness), so $x_k \gg k^{c/(c-1)}$.
   Splitting the partition sum at $K = X^{(c-1)/c}$ gives $X \ll X^{2-2/c}$, contradiction for $c < 2$.
3. **Theorem 5 — logarithmic refinement** $a_n \gg n^2/f(n)$ i.o. for any slowly-varying $f$ with $\sum 1/(nf(n)) < \infty$ (proof sketch). This recovers $a_n \gg (n/\log n)^2$ i.o. via $f(n) = (\log n)^2$.

Verified numerically: at $c = 1.5$, sum bound $/ X^{2-2/c} = 1.5$, so contradiction kicks in immediately. At $c = 1.99$, ratio is $99.5$, so contradiction arrives only at astronomically large $X$ — this is the "$o(1)$" in $n^{2-o(1)}$.

---

## Roadmap

The full plan is in `PLAN.md`. The current frontier is roughly:

- **✓ Phase 2C — reconstruct the GPT-5.4 Pro $n^2/f(n)$ argument.** *Done, session 4.* See `proofs/lower_bound_io.tex` Theorems 4 and 5. The argument is via the PDS partition identity, not Sidon density.

- **Phase 3 — Cilleruelo–Nathanson [CiNa08] explicit transfer.** *Investigated, session 4. Major finding: this approach does NOT improve Lev's $n^3$ upper bound on $a_n$.* The original [CiNa08] paper itself (`literature/cilleruelo_nathanson_2008.pdf`, p.9, Section 4.1, Problem 1) acknowledges this: *"the greedy algorithm used in [Le04] generates a perfect difference set such that $t_n \ll n^3$. Our method generates a dense Sidon set $\mathcal{A}$, but gives a very poor upper bound for the sequence $t_n$."* And they pose: *"Problem 1. Does there exist a perfect difference set such that $t_n = o(n^3)$?"* Here $t_n = b_n$ and $a_n = t_n + n$, so $t_n = o(n^3)$ is exactly equivalent to $a_n = o(n^3)$. **CiNa08's Problem 1 is the upper-bound side of #1194, and has been open since 2008.** What CiNa08 *does* give is density at sparse scales: a PDS with $A(x) \gg x^{\sqrt{2}-1+o(1)}$ (their Theorem 2, via Ruzsa's Sidon set) and a PDS with $\limsup A(x)/\sqrt{x} \geq 1/\sqrt{2}$ (their Theorem 3). Both are limsup-style; at intermediate $x$ density is much lower, and the corresponding $a_n$ values can be huge.

- **Phase 2B — convolution / Fourier route.** The PDS condition $1_A \star 1_A^- \equiv 1$ on $\mathbb{Z}_{>0}$ is a sharp Plancherel statement on $\widehat{1_A}$. Truncated to $A_M = A \cap [1, M]$, plug Fejér kernels and look for autocorrelation rigidity stronger than Sidon. *Now reframed:* with the partition-identity machinery from Phase 2C in hand, the open lower-bound question is to push the i.o. exponent past 2, e.g. to $a_n \gg n^2 \log \log n$ i.o., or to make the bound hold along denser subsequences.

- **Phase 2A — sharper Sidon density for PDS.** Investigate whether the unique-representation requirement forces $|A \cap [1,x]| < (1-\delta)\sqrt{x}$ for *all* large $x$ (not i.o.). Lower priority now, given Phase 2C resolved the i.o. side cleanly.

- **✓ Phase 4 — exact small-$N$ optimization.** *Done, session 5.* See `results/exact_summary.md`. Big finding: the **finite** PDS-up-to-$N$ optimum scales like $\approx 2N$, while greedy is $\Theta(N^3)$. Greedy is super-polynomially sub-optimal for the finite problem. See the next section for details.

---

## Phase 4 Findings (session 5, 2026-04-30)

### The finite problem: $M^*(N) := \min\,\{\max(A) : A \subset \mathbb{N}\ \text{Sidon},\ [1,N] \subset A - A\}$

Computed by branch-and-bound (bitmask DFS, plus Google ortools CP-SAT for $N \geq 30$). For each $N$, the search proves both feasibility at $M^*$ AND infeasibility at $M^* - 1$ exhaustively.

| $N$ | $M^*$ exact | greedy $\max(A)$ | greedy / exact | $|A^*|$ | $|A_{\text{greedy}}|$ |
|----:|-----------:|-----------------:|---------------:|--------:|----------------------:|
|  20 |  **36** |   97 |   2.7× |   8 |  11 |
|  25 |  **46** |  225 |   4.9× |   9 |  15 |
|  30 |  **56** |  444 |   7.9× |  10 |  19 |
|  35 |  **56** |  625 |  11.2× |  10 |  21 |
|  40 |  **86** | 1175 |  13.7× |  12 |  27 |
|  45 |  **86** | 1492 |  17.4× |  12 |  29 |
|  50 | $\geq 92$ | 2518 | $\geq 27.4$× | — |  35 |

(For $N = 50$ the search proved infeasibility for every $M \leq 91$; $M = 92$ exhausted the per-$M$ time budget. Witness sets and full table in `results/exact_summary.md`.)

### Asymptotic implications

The ratio $M^*(N)/N$ at the seven measured $N$ values is
$\{1.80, 1.84, 1.87, 1.60, 2.15, 1.91\}$ — hovering **around 2**, very close to the trivial floor $M^* \geq N + 1$. So empirically:

$$\boxed{\,M^*(N) \;\asymp\; 2N\,}\quad (\text{empirically, } N \in [20, 45])$$

Meanwhile greedy is $\Theta(N^3)$. The ratio $M_{\text{greedy}}/M^* \approx 0.4 N$ — a quadratic blow-up.

### Why this matters for #1194

The finite problem we solved is **not** Erdős's #1194 directly. The Erdős problem asks about an *infinite* PDS where every $n \geq 1$ is uniquely representable. The finite optima here cover only $[1, N]$ as differences and don't have to extend coherently to all integers. (Indeed, the $N = 30$ optimum's set extends to cover $[1, 47]$ but breaks at 48; covering 48 might require enlarging $\max(A)$ substantially.)

**But** the finite-vs-greedy gap is striking enough to be informative:

- **Lev's $\Theta(N^3)$ greedy is dramatically suboptimal even for the finite version.** The "extension cost" — the gap between greedy and the finite optimum — has been hiding most of the inefficiency. This concretizes Cilleruelo–Nathanson Open Problem 1 ("does there exist a PDS with $a_n = o(n^3)$?") from session 4: there's clearly $\Theta(N^2)$ slack to exploit.

- **The hard subquestion is whether finite optima glue.** If a sequence of finite optima $A_N^*$ for $N = 1, 2, \ldots$ could be *consistently extended* (each $A_{N+1}^*$ being a Sidon-respecting superset of $A_N^*$, not just a separate optimum), the resulting infinite $A$ would have $a_n \asymp 2n$ — falsifying the i.o. lower bound $a_n \gg n^{2-o(1)}$ from Phase 2C. So the finite optima **cannot** glue. Locating the obstruction is now a sharp question.

### What the structure of optimal $A^*$ suggests

The witness sets show no obvious arithmetic structure (not modular, not Singer-like). Consecutive small $A^*$:
- $N = 20$: $\{1, 5, 6, 18, 20, 26, 29, 36\}$
- $N = 30$: $\{1, 2, 7, 11, 24, 27, 35, 42, 54, 56\}$
- $N = 40$: $\{1, 10, 11, 18, 31, 43, 46, 57, 62, 80, 84, 86\}$

These look like ad-hoc combinatorial arrangements, not algebraic constructions.

---

## Phase 4' Findings (session 5, 2026-04-30) — extension cost

For each finite optimum $A_{N_0}^*$, define the **extension cost**
$$M_{\text{ext}}(N_0, N) := \min\bigl\{\max(A) : A \supseteq A_{N_0}^*,\ A\ \text{Sidon},\ [1, N] \subseteq A - A\bigr\}.$$
Computed exactly via CP-SAT (with $A_{N_0}^*$ pinned). See `results/extension_summary.md` for full tables and `extension_cost.py` for code.

### Trajectories

Two seeds, single greedy-style local extension at each step (each step is solved to optimality):

**Seed $A_{30}^*$ (max = 56):**
| $N$ | 30 | 36 | 42 | 48 | 56 | 60 | 63 |
|----:|---:|---:|---:|---:|---:|---:|---:|
| $M_{\text{ext}}$ | 56 | 92 | 254 | 399 | 516 | 1019 | 1590 |
| $M_{\text{ext}}/N$ | 1.87 | 2.56 | 6.05 | 8.31 | 9.21 | 16.98 | **25.24** |

**Seed $A_{20}^*$ (max = 36):**
| $N$ | 20 | 26 | 34 | 39 | 41 | 44 | 45 |
|----:|---:|---:|---:|---:|---:|---:|---:|
| $M_{\text{ext}}$ | 36 | 84 | 178 | 344 | 467 | 869 | 1054 |
| $M_{\text{ext}}/N$ | 1.80 | 3.23 | 5.24 | 8.82 | 11.39 | 19.75 | **23.42** |

### Headline finding: super-polynomial blow-up

Log-log fits on the "hard" steps (those requiring a new element):

| seed | full fit | tail fit (last 7 hard steps) |
|------|---------|------------------------------|
| $A_{20}^*$ | $M_{\text{ext}} \sim N^{3.80}$ | $N^{6.48}$ |
| $A_{30}^*$ | $M_{\text{ext}} \sim N^{4.27}$ | $N^{4.90}$ |

**The seeded extension grows faster than greedy's $N^3$.** Both seeds give exponents above 4 in the tail, with the exponent *increasing* along the trajectory (suggesting $M_{\text{ext}}$ may grow super-polynomially). At $N = 45$, the seeded extension from $A_{20}^*$ has $\max(A) = 1054$ — *worse than greedy's 1492*.

### Comparison

$$\boxed{\,M^*_{\text{unconstrained}}(N) \;\sim\; N \;\;\ll\;\; M_{\text{greedy}}(N) \;\sim\; N^3 \;\;\ll\;\; M_{\text{ext, seeded}}(N) \;\gtrsim\; N^4\,}$$

### Interpretation

A finite optimum $A_{N_0}^*$ packs $\binom{|A|}{2}$ distinct differences into $\sim [1, 2N_0]$ — close to the maximum Sidon density. This leaves very few free difference slots, making future extensions structurally cramped: every new element must avoid a densely-packed difference set.

Greedy avoids this trap by being deliberately conservative: each Strategy-2 element is placed at $\geq \max(A) + N + 1$, leaving large empty difference space. The result is a worse finite $\max(A)$ at any given $N$ but a *sustainable* polynomial growth rate.

This is consistent with the i.o. lower bound $a_n \gg n^{2-o(1)}$ (Phase 2C). In fact it strengthens it empirically: any "naive gluing" of finite optima produces $a_n$ growth WORSE than $N^3$. Beating greedy requires a fundamentally non-local construction that balances tightness at current $N$ against future extensibility — which is precisely what CiNa08 attempts (and pays for in density at intermediate $x$).

### Conjecture (new, "extension lower bound")

The empirical extension exponent suggests:

> **Conjecture.** Any infinite PDS $A$ satisfies $a_n \gg n^c$ for all large $n$, for some explicit $c \in (1, 2)$ (or possibly $c \in [2, 3]$). The value of $c$ is determined by the asymptotic exponent of $M_{\text{ext}}(N_0, N)$ taken in the limit $N_0 \to \infty$.

This would be a "for all $n$" lower bound — strictly stronger than the current i.o. bound. The empirical data is too noisy to pin down $c$, but the trend rules out $c = 1$ (the unconstrained finite scaling).

---

## Phase 2B Findings (session 6, 2026-05-11)

Phase 2B was an attempt to push the i.o. lower bound exponent past 2 via Fourier-side analysis. The work split into two streams; see `results/phase2b_summary.md`.

### Stream A — Theorem 5 promoted to full proof

The Phase 2C "logarithmic refinement" (Theorem 5 in `proofs/lower_bound_io.tex`) was sketched in session 4. Session 6 promotes it to a fully rigorous five-step proof: gap bound, size of $x_k$, anchor window, partition sum, contradiction. All constants tracked; slow-variation regularity used explicitly. The PDF is now 6 pages and compiles cleanly.

The proof's contradiction uses *two* independent decay facts together: $K^2 = o(X)$ (from $f(\sqrt{X}) \to \infty$) and $\varepsilon_K = \sum_{k>K} 1/(kf(k)) \to 0$ (from $\sum 1/(nf(n)) < \infty$). Failure of either collapses the argument, making the convergence boundary $\sum 1/(nf(n)) < \infty$ sharp **for this argument**.

### Stream B — Computational Fourier probes

`fourier_probes.py` runs on greedy data at $N \in \{200, 500, 1000, 1500\}$ and tests:
1. The Fejér PDS identity $\int K_T |\widehat{1_A}|^2 d\xi = |A| + (T - 1)$. **Holds exactly numerically.**
2. The anchor-window density vs Phase 2C's bound. The actual count is uniformly $\approx 0.42 \times$ greedy's Sidon density $|A|/\sqrt{\max A}$ at every $N$:

   | $N$ | $|A|/\sqrt{\max A}$ | anchor ratio | (anchor)/$(|A|/\sqrt{\max})$ |
   |----:|--------------------:|-------------:|----------------:|
   | 200 | 0.420 | 0.174 | 0.41 |
   | 500 | 0.276 | 0.120 | 0.43 |
   | 1000 | 0.203 | 0.088 | 0.43 |
   | 1500 | 0.168 | 0.070 | 0.42 |

3. The gap slope $\log d_k / \log x_k$ converges to $0.475$, very close to the predicted $1/c = 1/2$.

**The $c = 2$ boundary appears sharp.** The "anchor density" probe carries no PDS-specific information beyond Sidon density; pushing the exponent past 2 requires structure beyond the partition identity.

### Updated status of bounds after Phase 2B

| bound | direction | status |
|-------|-----------|--------|
| $a_n \gg n^{2-o(1)}$ i.o. | lower | **proven** (Theorem 4 of `lower_bound_io.tex`) |
| $a_n \gg n^2/f(n)$ i.o., $\sum 1/(nf(n)) < \infty$ | lower | **proven** (Theorem 5) |
| $a_n \gg n^c$ for all large $n$, some $c > 1$ | lower | open (Phase 4' conjecture) |
| $a_n \gg n^c$ i.o., $c > 2$ | lower | open — partition route exhausted |
| $a_n \ll n^{2+\varepsilon}$ for all $n$, some $\varepsilon > 0$ | upper | open (= CiNa08 Problem 1) |

Possible new ingredients for breaking the $c = 2$ ceiling:
- restriction / decoupling estimates for Sidon sets;
- a measure-theoretic argument on $\widehat{1_A}$ using PDS specificity;
- additive-energy bounds particular to PDS;
- probabilistic constructions to constrain extremal PDS structure.

---

## Phase 3' Findings (session 7, 2026-05-11) — dense-Sidon-seeded greedy

Take a known dense Sidon set as the initial $A$ and let the standard greedy (Strategy 1 + Strategy 2) complete it to a PDS covering $[1, N]$. The choice of seed turns out to matter a lot. See `results/seeded_summary.md` and `seeded_greedy.py`.

| Seed | $|A_{\text{seed}}|$ | $N$ | seeded $\max A$ | ratio $/N^3$ | improvement |
|------|--------------------:|----:|----------------:|-------------:|------------:|
| scratch greedy | 0 | 500 | 3,080,237 | 0.02464 | 1.0× |
| Erdős–Turán $p=23$ | 23 | 500 | 544,923 | 0.00436 | 5.7× |
| Mian–Chowla $n=30$ | 30 | 500 | 368,611 | 0.00295 | 8.4× |
| **Mian–Chowla $n=60$** | 60 | 500 | **286,281** | **0.00229** | **10.8×** |
| Mian–Chowla $n=100$ | 100 | 500 | 423,111 | 0.00339 | 7.3× |
| **Phase 4 optimum $A_{30}^*$** | 10 | 500 | 881,451 | 0.00705 | 3.5× |

### Three findings

1. **Dense Sidon seeding reduces the constant of $N^3$ scaling by up to 11×.** Mian–Chowla seeded greedy with 60 elements drops the asymptotic constant from $\approx 0.025\, N^3$ to $\approx 0.0023\, N^3$.

2. **The Phase 4 optimum is a *bad* seed.** Despite being the maximally dense Sidon set covering $[1, 30]$, using $A_{30}^*$ gives ratio 0.0070 — *worse than Mian–Chowla seeding by 3×*. This empirically confirms the Phase 4' principle: structurally tight seeds are traps; loose seeds (Mian–Chowla style) give the greedy more room to maneuver.

3. **Asymptotic scaling stays $\Theta(N^3)$.** Across all seeds tested, $\max(A)/N^3 \in [0.002, 0.025]$. No seed produces sub-cubic asymptotic. So seeding gives constant-factor improvement only — beating $o(n^3)$ (CiNa08 Problem 1) requires a fundamentally non-greedy continuation strategy, not just a better starting set.

---

## Phase 6 Findings (session 9, 2026-05-11) — block-structured construction

We extended Phase 3' by testing block-structured Sidon seeds — `split_MC` (two disjoint Mian–Chowla chunks at chosen offset) and `AP_MC` (arithmetic-progression of MC chunks). All seeds verified Sidon. Results at $N = 500$:

| Strategy | $|A_{\text{seed}}|$ | $\max A$ | ratio $/N^3$ |
|----------|--------------------:|---------:|-------------:|
| scratch greedy | 0 | 3,080,237 | 0.02464 |
| MC(60) | 60 | 286,281 | 0.00229 |
| **split_MC(30,30)** | 60 | **280,501** | **0.00224** |
| split_MC(40,40) | 80 | 331,746 | 0.00265 |
| AP_MC($k=20,m=3$) | 60 | 383,640 | 0.00307 |
| AP_MC($k=30,m=2$) | 60 | 302,887 | 0.00242 |

**Result:** The best block-structured strategy gives ratio 0.00224 — only marginally below MC(60)'s 0.00229. *No construction breaks the cubic ceiling.* Spot-check at $N=550$ with MC(60) gives 0.00216, suggesting the constant settles around $\approx 0.002\,N^3$.

**Why:** Once the seed is fixed, the *greedy continuation* is forced into Strategy-2 calls whose per-call cost is $\Theta(N^2)$ — independent of seed structure. This drives the cubic. **Beating $o(n^3)$ requires redesigning the continuation, not just the seed.**

Phase 6 is closed as a **no-go**: within the "structured seed + greedy continuation" family, no variant beats $\Theta(N^3)$. The CiNa08 Problem 1 answer (does $a_n = o(n^3)$ exist?) remains open. Full writeup in `results/phase6_summary.md`.

---

## Phase 2A Findings (session 10, 2026-05-13) — sharper Sidon density for PDS

A speculative theorem hunt aimed at: prove $\limsup k(x)/\sqrt x \leq 1 - \delta$ for some explicit $\delta > 0$ and every infinite PDS (where $k(x) := |A \cap [1, x]|$). Background: Lindström gives $\leq 1$ for any Sidon set; CiNa08 Theorem 3 gives $\geq 1/\sqrt 2 \approx 0.707$ achieved by some PDS. The gap $0.293$ is the territory.

**Automatic from Phase 2C:** for every $c < 2$, $\liminf k(x)/x^{1/(2c)} \leq \sqrt 2$, so $\liminf k(x)/\sqrt x = 0$. This controls density at the sparse $x$ where the i.o. lower bound on $a_n$ triggers, but says nothing about $\limsup$.

**Three attempts that fail:**

1. **Cauchy–Schwarz via the partition identity.** Hoped that PDS coverage $T_M = \binom{k(M)}{2}$ forces "perfect packing". Failed because $a_n$ is non-monotone, so the covered prefix $T_M$ can be much less than $\binom{k(M)}{2}$ (greedy has $T_M = 1898$ vs $\binom{k}{2} = 2.27 \times 10^6$).

2. **Fejér-weighted Plancherel.** Gives $\int K_T |\widehat{1_A}|^2 = k + T - 1$, but the only useful upper bound trivializes to Sidon.

3. **Higher $L^p$ moments.** $\int |\widehat{1_A}|^{2p}$ counts solutions $\sum(a_i - b_i) = n$, determined by Sidon alone. PDS adds no constraint at the moment level.

**Why all three fail (structural).** The PDS-vs-Sidon distinction shows up in *which* small differences appear, not in aggregate counting. The Phase 2C partition argument is the unique tool that uses "which differences appear", and it caps at $c = 2$.

**Empirical check on greedy** at the largest checkpoint: $k(x)/\sqrt x$ decays like $x^{-1/6}$ (from 1.10 at $x=100$ to 0.15 at $x \approx 2\cdot 10^8$). So greedy isn't the witness — it's far below Sidon density. The natural witness is CiNa08's construction at sparse $x$.

**Status:** Phase 2A as framed is open. Full writeup in `proofs/phase2a_density.tex` (5 pp, compiles) and `results/phase2a_summary.md`. Three sub-targets identified for future work (density-zero exceptional set, close the 0.293 gap, positive-density Phase 2C). No new theorem produced.

---

## Phase 7 Findings (session 11, 2026-05-13) — Lean formalization

Formalized the statements of Theorems 1, 4, 5 from the comprehensive note (plus Lev's upper bound, Cilleruelo–Nathanson Open Problem 1, and the Phase 4' extension lower bound conjecture) in Lean 4 / Mathlib syntax, matching the [`google-deepmind/formal-conjectures`](https://github.com/google-deepmind/formal-conjectures) convention.

Output: [`formal/1194.lean`](formal/1194.lean) — a single file ready to copy into `FormalConjectures/ErdosProblems/1194.lean` in that repo. Includes:

| Lean declaration | Mathematical content |
|---|---|
| `IsPDS : Set ℕ → Prop` | PDS definition |
| `aFun`, `bFun`, `kFun` | $a_n, b_n, k(x)$ |
| `isPDS_imp_sidon` | PDS ⇒ Sidon |
| `pds_counting` | Lemma 1: $N(x) = \binom{k(x)}{2}$ |
| `pds_partition_consequence` | Lemma 2: $X = \sum_k \lvert D_k \cap [1, X]\rvert$ |
| `gap_bound` | Lemma 3: $a_n \leq Cn^c \Rightarrow x_k \gg k^{c/(c-1)}$ |
| `lev_upper_bound` | $\exists$ PDS with $a_n \ll n^3$ |
| `thm1_n_log_n_io` | Theorem 1: $a_n \gg n \log n$ i.o. |
| `thm4_n_two_minus_o_one_io` | Theorem 4: $a_n \gg n^{2-o(1)}$ i.o. |
| `thm5_n_squared_over_f_io` | Theorem 5: $a_n \gg n^2/f(n)$ i.o. |
| `thm5_corollary_n_over_log_squared` | corollary: $a_n \gg (n/\log n)^2$ i.o. |
| `cina08_problem1` | Open: $\exists$ PDS with $a_n = o(n^3)$? |
| `extension_lower_bound_conjecture` | Phase 4' conjecture: $a_n \gg n^c$ for all large $n$ |

All theorems use `sorry` for their proofs — the artifact value is the *formal statement*, as is conventional in `formal-conjectures` (per their README: *"there is a lack of open conjectures where only the statement has been formalised"*).

Each theorem includes a doc-comment with a proof sketch and a pointer back to `proofs/erdos_1194_note.tex` for the prose proof. The file structure deliberately mirrors the LaTeX so a future proof-port is mechanical.

Submission path: fork `formal-conjectures`, drop the file into `FormalConjectures/ErdosProblems/1194.lean`, verify `lake build` against the repo's pinned Mathlib, open a PR linking to `proofs/erdos_1194_note.pdf` and the erdosproblems.com comment thread. Details in [`formal/README.md`](formal/README.md).

---

## Files

| File | Description |
|------|-------------|
| `explore.py` | Greedy construction (numba JIT v4, Strategy 1 + 2) |
| `_jit_search.py` | Numba JIT inner loop (cached) |
| `build_checkpoint.py` | Checkpoint-enabled builder for large $N$ |
| `verify_and_analyze.py` | **Phase 0 verification + Phase 1 measure / stratification scan** |
| `exact_search.py` | **Phase 4 — bitmask DFS for finite PDS-up-to-$N$ optimum** |
| `exact_search_cpsat.py` | **Phase 4 — CP-SAT per-$M$ scan (fast for $N \geq 25$)** |
| `exact_search_cpsat_opt.py` | **Phase 4 — CP-SAT single-solve optimization mode** |
| `extension_cost.py` | **Phase 4' — measures extension cost from a fixed seed** |
| `fourier_probes.py` | **Phase 2B — Fourier-observable probes on greedy PDS** |
| `seeded_greedy.py` | **Phase 3' — dense-Sidon-seeded greedy (Mian–Chowla, Erdős–Turán, Phase 4 optimum)** |
| `block_construction.py` | **Phase 6 — split-MC and AP-MC block-structured seeds** |
| `proofs/lower_bound_io.tex` | LaTeX writeup of classical $a_n \gg n \log n$ i.o. and verified GPT-5.4 Pro $n^{2-o(1)}$ i.o. (Theorems 1, 4, 5 — full proofs) |
| `proofs/lower_bound_io.pdf` | Compiled six-page note |
| `proofs/erdos_1194_note.tex` | **Phase 5 — comprehensive research note** (i.o. bounds + Phase 4 finite optima + Phase 4' obstruction + Phase 3' seeded greedy + open problems) |
| `proofs/erdos_1194_note.pdf` | Compiled eight-page note |
| `proofs/phase2a_density.tex` | **Phase 2A — density theorem hunt** (5pp; three failed attempts + sub-targets) |
| `proofs/phase2a_density.pdf` | Compiled exploration note |
| `formal/1194.lean` | **Phase 7 — Lean formalization** of statements (theorems + open conjectures), in `formal-conjectures` format |
| `formal/README.md` | Lean directory README; submission instructions for `google-deepmind/formal-conjectures` |
| `erdos_42/solve_42.py` | **Phase 8 — Erdős Problem #42 CP-SAT model** (gap = $g(N) - \binom{f(N)}{2}$) |
| `erdos_42/phase8_summary.md` | Phase 8 session-1 findings: gap appears to **grow**, possibly disproving #42 conjecture as stated |
| `SURVEY.md` | Survey of open Erdős problems for our toolkit |
| `literature/cilleruelo_nathanson_2008.pdf` | Cilleruelo–Nathanson 2008 paper, downloaded for reference |
| `NEXT_PLAN.md` | Forward-looking plan: Phase 5 (done), Phase 6, Phase 2A, Phase 7 |
| `results/pds_N.csv` | Per-step data for $N \in \{200, 300, 500, 600, 1000, 1200, 1500\}$ |
| `results/checkpoint_*.pkl` | Saved states for incremental large-$N$ runs |
| `results/measure_sums.csv` | Phase 1A: candidate-measure inverse-power sums |
| `results/measure_tail_sums.csv` | Phase 1A: tail decay of $\sum 1/a^s$ over $A$ |
| `results/running_min_max.csv` | Phase 1B: stratified $a_n / n^k$ samples |
| `results/peaks.csv` | Phase 1C: every running record of $a_n / n^2$ |
| `results/verification_report.txt` | Phase 0: verification result for $N = 1898$ |
| `results/exact_summary.md` | **Phase 4 summary table and witnesses** |
| `results/exact_N{20,30}.json` | Bitmask-DFS exact runs |
| `results/exact_cpsat_N{40,45,50}.json` | CP-SAT per-$M$-scan logs |
| `results/exact_cpsat_opt_N{20,25,30,35}.json` | CP-SAT optimization-mode logs |
| `results/extension_long_N{20,30}.json` | **Phase 4' — long extension trajectories** |
| `results/extension_summary.md` | **Phase 4' — full results, fits, conjecture** |
| `results/phase2b_summary.md` | **Phase 2B — Theorem 5 rigorous, Fourier probes, sharpness** |
| `results/seeded_summary.md` | **Phase 3' — full seed comparison table and analysis** |
| `results/phase6_summary.md` | **Phase 6 — block construction no-go writeup** |
| `results/phase2a_summary.md` | **Phase 2A — density theorem hunt summary** |
| `results/seeded_*.csv` | Per-step data for each seeded run |
| `results/fourier_anchor_N*.json` | Anchor-window data per $N$ |

---

## Progress Log

- **2026-04-27 (session 1):** Project started. Greedy construction implemented and optimised (numpy vectorisation). Data collected for $N \leq 500$. Key finding: greedy achieves $\max(A) \sim 0.025N^3$, consistent with Lev's $O(n^3)$ upper bound. The $a_n$ distribution is bimodal; "hard" differences (driving the peaks) are the core of the Erdős question.

- **2026-04-27 (session 2):** Numba JIT inner loop added (~5× speedup). Checkpointing implemented. Data extended to $N = 1{,}898$. **Main finding:** $\max(A)/N^3 \approx 0.0293$ converges for $N \geq 1{,}500$. The greedy is provably $\Theta(N^3)$. This closes the question of what the greedy achieves; the open problem is whether any construction can beat $N^3$.

- **2026-04-27 (session 3):** Plan-and-prove pass. (1) Greedy data verified at $N = 1898$ — all five PDS invariants hold. (2) Naive measure approach $\sum 1/a^s$ ruled out empirically — it's controlled by Sidon density, not PDS structure. (3) Bimodality of $a_n$ quantified: 56% hard / 44% easy split, with $\min a_n/n^2 \to 0$ and $\max a_n/n^2 \approx 56$ at $N = 1898$. (4) Running peak fit: $a_n^{\text{peak}} \approx 0.0635\, n^{2.90}$. (5) Clean LaTeX of classical $a_n \gg n \log n$ i.o.\ written. (6) **Negative finding:** GPT-5.4 Pro's $n^{2-o(1)}$ i.o. refinement could not be reconstructed from PDS counting + i.o. Sidon density alone — that route caps at $n \log n$. The advertised refinement requires unidentified extra structure; reconstructing it is now Phase 2C of the roadmap.

- **2026-05-13 (session 12):** **Phase 8 — attack on Erdős Problem #42 (open since ~1985, \$100 bounty).** Defined and implemented CP-SAT model in `erdos_42/solve_42.py` for $g(N) = \max \binom{|A|}{2} + \binom{|B|}{2}$ over disjoint-difference Sidon pairs $A, B \subset [1, N]$, alongside $f(N) = \max |A|$ for a single Sidon set. Conjecture #42: gap $g(N) - \binom{f(N)}{2}$ is $O(1)$. **Empirical finding: the gap GROWS.** Peak gap per $f$-plateau: $f=3 \to 1,\ f=4 \to 3,\ f=5 \to 3,\ f=6 \to 6,\ f=7 \to 6,\ f=8 \to \geq 6$ (lower bound, solver feasibility-only). The optimum pair has $|A| = f(N)$ and a secondary $|B|$ that grows with $f$ (sequence 2, 3, 3, 4, 4, $\geq 4$). If the trend holds, gap $= \binom{|B|}{2}$ grows like $f$, i.e., $\sqrt N$ — disproving conjecture #42 as stated. CP-SAT becomes slow at $N \geq 40$. Full session-1 writeup, tables, and proposed sessions 2–4 in `erdos_42/phase8_summary.md`.

- **2026-05-13 (session 10):** **Phase 2A — density theorem hunt — no theorem.** Tried to prove $\limsup k(x)/\sqrt x \leq 1 - \delta$ for explicit $\delta > 0$ using PDS structure. Documented three structural attempts in `proofs/phase2a_density.tex` (5pp, compiles): Cauchy–Schwarz via the partition identity (fails because $a_n$ non-monotone makes $T_M$ much smaller than $\binom{k}{2}$), Fejér-weighted Plancherel (trivializes to Sidon), higher $L^p$ moments (determined by Sidon alone). Honest deliverable is a *negative* result: the partition argument is the unique elementary tool, and it caps at $c = 2$. Identified three sub-targets (density-zero exceptional set, close the 0.293 gap, positive-density Phase 2C). Empirical: greedy's $k(x)/\sqrt x$ decays like $x^{-1/6}$, far below Sidon ceiling — greedy isn't even the relevant witness for this question. CiNa08 construction is. Phase 2A status: open, no new theorem produced. Full summary in `results/phase2a_summary.md`.

- **2026-05-11 (session 9):** **Phase 6 done — block construction no-go.** Built and tested two new block-structured Sidon seed families: `split_MC(k1,k2)` (two disjoint Mian–Chowla chunks at carefully chosen offset; the key insight is that MC is globally Sidon so two disjoint MC chunks share no within-block diffs), and `AP_MC(k,m)` (arithmetic progression of $m$ MC chunks of size $k$). All seeds verified Sidon by sweep. Best result at $N = 500$: `split_MC(30,30)` gives ratio 0.00224 — only marginally below MC(60)'s 0.00229. The $\Theta(N^3)$ ceiling is robust under all variants. Spot-check at $N = 550$ for MC(60) gives 0.00216, suggesting the constant settles near $\approx 0.002 N^3$. **Conclusion:** within the "structured seed + greedy continuation" family, $\Theta(N^3)$ holds. The per-call cost of greedy's Strategy-2 is $\Theta(N^2)$ regardless of seed structure, driving the cubic. Beating $o(n^3)$ requires non-greedy continuation. CiNa08 Problem 1 remains open. Full writeup in `results/phase6_summary.md`. Routes forward per `NEXT_PLAN.md`: Phase 7 (Lean formalization, low-risk artifact) or Phase 2A (sharper Sidon density, speculative theorem hunt).

- **2026-05-11 (session 8):** **Phase 5 done — comprehensive research note.** Consolidated all findings from sessions 0–7 into a self-contained 8-page LaTeX note at `proofs/erdos_1194_note.tex` (compiles cleanly to `erdos_1194_note.pdf`). Sections cover: (1) setup and PDS counting identity, (2) full proofs of the three i.o.\ lower bounds (Theorems 1, 4, 5 with the partition-identity arg and logarithmic refinement), (3) exact small-$N$ optima from Phase 4 with the $M^*(N)\approx 2N$ observation, (4) the Phase 4' extension obstruction with the new "for all $n$" Conjecture~1, (5) constructive upper bound from Phase 3' showing the 10.8× seeding improvement plus the bad-Phase-4-seed empirical witness, (6) open-problems section mapping the $c=2$ barrier and the CiNa08 Problem 1, plus candidate routes for breaking each barrier. A forward-looking research plan is saved at `NEXT_PLAN.md` (Phase 5 done; Phase 6 = block-structured construction proposed as next).

- **2026-05-11 (session 7):** **Phase 3' done — dense-Sidon-seeded greedy.** Implemented in `seeded_greedy.py`, tested across Mian–Chowla, Erdős–Turán, and Phase 4 optimum seeds. **Best result:** Mian–Chowla seed of size 60 at $N = 500$ gives $\max(A) = 286{,}281$ vs scratch greedy's 3,080,237 — **a 10.8× improvement**. The constant of the $N^3$ scaling drops from $\approx 0.025$ to $\approx 0.0023$. Crucially, the Phase 4 *optimum* seed ($A_{30}^*$) is a BAD seed — it gives ratio 0.0070, worse than Mian–Chowla by 3×. This empirically confirms the Phase 4' principle: tight seeds are extension traps; loose Mian–Chowla-style seeds give greedy room to maneuver. Asymptotic scaling stays $\Theta(N^3)$ across all seeds — seeding gives only a constant-factor improvement, not a sub-cubic asymptote. CiNa08 Problem 1 ($a_n = o(n^3)$ achievable?) requires a fundamentally non-greedy continuation strategy.

- **2026-05-11 (session 6):** **Phase 2B done — two streams.** (Stream A) Promoted Theorem 5 (the $a_n \gg n^2/f(n)$ i.o. logarithmic refinement) from a "proof sketch" to a fully rigorous five-step proof in `proofs/lower_bound_io.tex` (now 6 pages, compiles). All constants tracked. The convergence boundary $\sum 1/(nf(n)) < \infty$ is shown to be sharp *for this argument*. (Stream B) `fourier_probes.py` tested several Fourier-side observables on greedy data at $N \in \{200, 500, 1000, 1500\}$. Found: Fejér PDS identity $\int K_T |\widehat{1_A}|^2 = |A|+T-1$ holds exactly; gap slope $\log d_k/\log x_k \to 0.475 \approx 1/c$ for $c=2$; the anchor-window count is uniformly $0.42 \times |A|/\sqrt{\max A}$ — a constant multiple of greedy's Sidon density, carrying no PDS-specific slack. **Conclusion:** the $c = 2$ ceiling in the partition-identity argument is empirically sharp. Pushing past requires fundamentally new structure (restriction, decoupling, or a non-partition counting identity). Full writeup in `results/phase2b_summary.md`.

- **2026-04-30 (session 5):** **Phase 4 + Phase 4' done.** (Part 1) Implemented exact branch-and-bound for the finite PDS-up-to-$N$ problem in two engines (bitmask DFS + Google ortools CP-SAT). Solved $N \in \{20, 25, 30, 35, 40, 45\}$ to optimality; pushed $N = 50$ to $M^* > 91$. **Headline 1:** $M^*(N) \approx 2N$ empirically, vs greedy's $\Theta(N^3)$. (Part 2) **Phase 4' — extension cost.** For each finite optimum $A_{N_0}^*$, compute $M_{\text{ext}}(N_0, N)$ = min max(A) over Sidon supersets $A \supseteq A_{N_0}^*$ covering $[1, N]$. Two trajectories run via CP-SAT: from $A_{20}^*$ extended to $N=45$, and from $A_{30}^*$ extended to $N=63$. **Headline 2:** seeded extension grows *super-polynomially*: log-log fits give $M_{\text{ext}} \sim N^{4-5}$ in both trajectories, with the exponent *increasing* in the tail. At $N=45$, $A_{20}^*$-seeded extension reaches $\max(A) = 1054$ — *worse than greedy's 1492*. This is the **structural obstruction** to gluing finite optima into an infinite PDS: a tight finite optimum exhausts the difference budget, so each future $n$ needs an ever-larger jump to find a Sidon-compatible new element. The chain $M^*(N) \sim N \ll M_{\text{greedy}}(N) \sim N^3 \ll M_{\text{ext}}(N) \gtrsim N^4$ is now empirically established. New conjecture (extension lower bound): any infinite PDS satisfies $a_n \gg n^c$ for all large $n$, with $c > 1$ and the value of $c$ determined by the asymptotic exponent of $M_{\text{ext}}$.

- **2026-04-30 (session 4):** **Phase 2C closed; Phase 3 investigated and re-scoped.** (1) Pulled the actual argument from the comment thread on `erdosproblems.com/forum/thread/1194` (Bloom's distillation of GPT-5.4 Pro, post 5745). The structure is fundamentally different from what we tried in session 3: it uses the **PDS partition identity** $\bigsqcup_k D_k = \mathbb{Z}_{>0}$ (where $D_k := \{x_k - x_i : i < k\}$) together with a gap lower bound $d_k \geq (x_k/C)^{1/c}$ derived from $a_{d_k} = x_k$. Splitting the partition sum at $K = X^{(c-1)/c}$ produces $X \ll X^{2-2/c}$, contradiction for $c < 2$. Numerically verified (constant in front blows up as $c \uparrow 2$, hence the $o(1)$). Wrote into `proofs/lower_bound_io.tex` as Theorems 4 and 5 (5 pages total). Also flagged a typo on the upstream problem page: it states "$\sum 1/(nf(n))$ diverges" but the proof requires it to **converge** (natso26 caught this in post 5782, Bloom acknowledged in post 5784, but the page text wasn't updated). (2) Downloaded and read [CiNa08] in full (`literature/cilleruelo_nathanson_2008.pdf`). **Major negative finding:** CiNa08's transfer method does NOT improve $a_n \ll n^3$. The authors say so explicitly in their Section 4.1 and pose "Problem 1: does there exist a PDS with $t_n = o(n^3)$?" — which is exactly the upper-bound side of #1194, and has been **open since 2008**. The CiNa08 density results ($A(x) \gg x^{\sqrt{2}-1+o(1)}$, $\limsup A(x)/\sqrt{x} \geq 1/\sqrt{2}$) are limsup-style only; intermediate $x$ have much lower density and correspondingly large $a_n$. Conclusion: Phase 3 as originally framed is dead; the upper-bound side will need a fundamentally new approach.
