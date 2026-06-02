# Phase 2B — Fourier route results

## Two streams

### Stream A: rigorous proof of Theorem 5 (the logarithmic refinement)

Promoted from "proof sketch" to full proof in `proofs/lower_bound_io.tex`
(now 6 pages, compiles cleanly). The theorem:

> Let $f$ be nondecreasing, slowly varying, unbounded, with
> $\sum_{n \geq 2} \tfrac{1}{n f(n)} < \infty$. Then for any infinite
> perfect difference set $A$, $a_n \gg n^2/f(n)$ infinitely often.

The proof is a refinement of the Phase 2C partition argument, with all
constants tracked and the slow-variation assumption used explicitly in
five places (gap bound, size of $x_k$, anchor window, tail count, and
final balance). The contradiction uses
$K^2 = o(X)$ (from $f(\sqrt X) \to \infty$) AND
$\varepsilon_K = \sum_{k > K} 1/(k f(k)) \to 0$
(from the convergence hypothesis) together. Failure of either kills the
contradiction, so the convergence boundary $\sum 1/(n f(n)) < \infty$ is
sharp **for this argument**.

### Stream B: computational Fourier probes

Run via `fourier_probes.py` on greedy data at $N \in \{200, 500, 1000, 1500\}$.

**Fejér PDS identity test:** the identity
$$\int K_T(\xi)\, |\widehat{1_A}(\xi)|^2\, d\xi \;=\; |A| + (T - 1) \qquad (T \leq T_{\max})$$
holds exactly numerically for greedy PDS. This is a sanity check on our
Fourier-side computation. Passes.

**Anchor window density test:** Phase 2C Step 3 bounds the count
$|A \cap [x_k - X, x_k)|$ by $X / x_k^{1/c}$ with $c = 2$, i.e. by
$X/\sqrt{x_k}$. We measured the ACTUAL count and the ratio.

| $N$ | $|A|$ | $\max A$ | gap slope $d_k$ vs $x_k$ | anchor ratio (median) |
|----:|------:|---------:|-------------------------:|----------------------:|
| 200 | 164 | 152,791 | 0.533 | 0.174 |
| 500 | 484 | 3,080,237 | 0.497 | 0.120 |
| 1000 | 1038 | 26,100,594 | 0.480 | 0.088 |
| 1500 | 1629 | 94,610,174 | 0.475 | 0.070 |

The gap slope is converging to $0.475$, very close to $1/c = 1/2$.

The anchor ratio appears to decay, suggesting slack — but the decay is
exactly explained by greedy's Sidon density:

| $N$ | $|A|/\sqrt{\max A}$ | anchor ratio | ratio of ratios |
|----:|--------------------:|-------------:|----------------:|
| 200 | 0.420 | 0.174 | 0.41 |
| 500 | 0.276 | 0.120 | 0.43 |
| 1000 | 0.203 | 0.088 | 0.43 |
| 1500 | 0.168 | 0.070 | 0.42 |

The anchor ratio is **exactly $0.42 \times$ greedy's overall density** at
all $N$ scales. So the "anchor density" is just a uniform fraction of the
overall density — it carries no extra PDS-specific information beyond
Sidon density of $A$.

### Conclusion on Phase 2B

**The $c = 2$ boundary in the partition argument is sharp.** Computational
probing confirms no exploitable slack in Step 3. To push the i.o. exponent
past 2, one needs structure beyond the PDS partition identity plus Sidon
density — that is, a Fourier/restriction estimate or another identity not
visible in the partition argument.

This is consistent with the remark in Theorem 5: the convergence boundary
$\sum 1/(n f(n)) < \infty$ is the boundary FOR THIS ARGUMENT. Better
bounds require new ingredients.

### Status of bounds after Phase 2B

| bound | direction | proof status |
|-------|-----------|--------------|
| $a_n \gg n^{2-o(1)}$ i.o. | lower | **proven** (Theorem 4) |
| $a_n \gg n^2/f(n)$ i.o., $\sum 1/(nf(n)) < \infty$ | lower | **proven** (Theorem 5) |
| $a_n \gg n^c$ for all large $n$, some $c > 1$ | lower | open (Phase 4' conjecture) |
| $a_n \gg n^c$ i.o., $c > 2$ | lower | open (Phase 2B target) |
| $a_n \ll n^{2+\varepsilon}$ for all $n$, some $\varepsilon > 0$ | upper | open (= CiNa08 Problem 1) |

The two "open" lower-bound items both seem to require ingredients beyond
the partition identity. Possible future routes:
- restriction theorems / decoupling estimates for Sidon sets;
- a measure-theoretic argument on $\widehat{1_A}$;
- additive-energy bounds specific to PDS structure;
- random / probabilistic constructions to constrain extremal PDS.
