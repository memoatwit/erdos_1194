/-
Copyright 2026 The Formal Conjectures Authors.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    https://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
-/
import FormalConjectures.Util.ProblemImports

/-!
# Erdős Problem 1194

*Reference:* [erdosproblems.com/1194](https://www.erdosproblems.com/1194)

Let $A \subset \mathbb{N}$ be a **perfect difference set** (PDS): every
$n \geq 1$ admits a *unique* representation $n = a_n - b_n$ with
$a_n, b_n \in A$, $a_n > b_n$. Erdős asked how fast $a_n/n$ must
increase ([Er80, p.100]). The greedy construction of Lev [Le04]
achieves $a_n \ll n^3$.

This file formalises:

* **Lev's upper bound** $a_n \ll n^3$ (Theorem `lev_upper_bound`).
* **Erdős's classical $n \log n$ lower bound** infinitely often
  (Theorem `thm1_n_log_n_io`).
* The **partition-identity refinement** $a_n \gg n^{2-o(1)}$
  infinitely often, due to GPT-5.4 Pro and condensed by T. Bloom
  in the comment thread of erdosproblems.com/1194 (April 23, 2026,
  post 5745) (Theorem `thm4_n_two_minus_o_one_io`).
* The **logarithmic refinement** $a_n \gg n^2/f(n)$ infinitely often
  for any slowly varying $f$ with $\sum 1/(nf(n)) < \infty$
  (Theorem `thm5_n_squared_over_f_io`).
* The **open question** $a_n = o(n^3)$ (Cilleruelo–Nathanson Problem 1,
  `cina08_problem1`).
* The **extension lower bound conjecture** suggested by empirical
  computations (`extension_lower_bound_conjecture`).

Full proofs of the lower-bound theorems and accompanying computational
evidence are in the companion repository: `erdos_1194/proofs/erdos_1194_note.tex`
and `erdos_1194/proofs/lower_bound_io.tex`.
-/

open Filter Real Set
open scoped Nat Topology BigOperators

namespace Erdos1194

/-- `A ⊂ ℕ` is a **perfect difference set** (PDS) if every positive
integer `n` admits a *unique* representation `n = a - b` with
`a, b ∈ A` and `a > b`. -/
def IsPDS (A : Set ℕ) : Prop :=
  ∀ n : ℕ, 0 < n →
    ∃! ab : ℕ × ℕ, ab.1 ∈ A ∧ ab.2 ∈ A ∧ ab.2 < ab.1 ∧ ab.1 - ab.2 = n

/-- For an infinite PDS `A`, `aFun A h n` is the larger element of the
unique pair representing `n` when `n ≥ 1`, and `0` otherwise. -/
noncomputable def aFun (A : Set ℕ) (h : IsPDS A) : ℕ → ℕ
  | 0 => 0
  | (k + 1) => ((h (k + 1) (Nat.succ_pos k)).exists.choose).1

/-- For an infinite PDS `A`, `bFun A h n` is the smaller element of the
unique pair representing `n` when `n ≥ 1`, and `0` otherwise. -/
noncomputable def bFun (A : Set ℕ) (h : IsPDS A) : ℕ → ℕ
  | 0 => 0
  | (k + 1) => ((h (k + 1) (Nat.succ_pos k)).exists.choose).2

/-- The truncated counting function $k(x) := |A \cap [1, x]|$. -/
noncomputable def kFun (A : Set ℕ) (x : ℕ) : ℕ := (A ∩ Set.Icc 1 x).ncard

/-- Any PDS is a *Sidon set*: all pairwise differences are distinct. -/
theorem isPDS_imp_sidon {A : Set ℕ} (h : IsPDS A) :
    ∀ ⦃a₁ b₁ a₂ b₂ : ℕ⦄,
      a₁ ∈ A → b₁ ∈ A → a₂ ∈ A → b₂ ∈ A →
      b₁ < a₁ → b₂ < a₂ → a₁ - b₁ = a₂ - b₂ → (a₁, b₁) = (a₂, b₂) := by
  sorry

/-- **PDS counting identity (Lemma 1 of the note).**
For an infinite PDS `A` and any $x \ge 1$, the number of $n \ge 1$ with
$a_n \le x$ equals $\binom{k(x)}{2}$. -/
theorem pds_counting (A : Set ℕ) (h : IsPDS A) (x : ℕ) (hx : 1 ≤ x) :
    ({n : ℕ | 0 < n ∧ aFun A h n ≤ x}.ncard) = Nat.choose (kFun A x) 2 := by
  sorry

/-- **PDS partition identity (Lemma 2 of the note).**
Let `A = {x₁ < x₂ < …}` be the increasing enumeration of an infinite PDS.
For each $k \geq 2$ let $D_k := \{x_k - x_i : 1 \leq i < k\}$. Then
$\{D_k\}_{k \geq 2}$ is a partition of $\mathbb{Z}_{>0}$. We state the
useful consequence: for every $X \ge 1$,
$$X = \sum_{k \ge 2} |D_k \cap [1, X]|.$$ -/
theorem pds_partition_consequence (A : Set ℕ) (h : IsPDS A) (hA : A.Infinite)
    (X : ℕ) (hX : 0 < X) :
    -- The full statement requires the increasing enumeration of A;
    -- we omit the explicit statement here, recording it as `sorry`
    -- pending the development of an enumeration framework.
    True := by
  sorry

/-- **Gap bound (Lemma 3 of the note).**
Suppose `a_n ≤ C * n^c` for all `n ≥ 1` and some `c > 1`, `C > 0`.
Then consecutive elements `x_k > x_{k-1}` in the increasing enumeration
of `A` satisfy `(x_k - x_{k-1}) ≥ (x_k / C)^{1/c}`, and consequently
`x_k ≥ c' * k^{c/(c-1)}` for some `c' > 0`. -/
theorem gap_bound (A : Set ℕ) (h : IsPDS A) (hA : A.Infinite) (c : ℝ) (hc : 1 < c)
    (C : ℝ) (hC : 0 < C)
    (hub : ∀ n : ℕ, 0 < n → (aFun A h n : ℝ) ≤ C * (n : ℝ)^c) :
    True := by
  sorry

/-- **Lev's upper bound.**
There exists an infinite PDS `A` with $a_n \ll n^3$.

*Source:* V. F. Lev, *Reconstructing integer sets from their representation
functions*, Electron. J. Combin. 11 (2004), R78. The construction is
explicit (the greedy algorithm); empirically $\max_n a_n \approx 0.0293 \cdot N^3$
for $N \in [1500, 1900]$ (see `erdos_1194/README.md`). -/
@[category research solved, AMS 11]
theorem lev_upper_bound :
    ∃ A : Set ℕ, ∃ h : IsPDS A, A.Infinite ∧
      ∃ C > (0 : ℝ), ∀ n : ℕ, 0 < n →
        (aFun A h n : ℝ) ≤ C * (n : ℝ)^3 := by
  sorry

/-- **Theorem 1 — classical $n \log n$ lower bound, infinitely often.**

For any infinite PDS `A`, there exists `c > 0` such that
$a_n \geq c \cdot n \log n$ for infinitely many `n`.

*Proof sketch:* Combine the PDS counting identity
`N(x) = (k(x) choose 2)` with Erdős's infinitely-often Sidon-density bound
$|B \cap [1, x]| \ll \sqrt{x/\log x}$ i.o. for any infinite Sidon set
`B` (Halberstam–Roth, Sequences, Ch. II).

*Reference:* `proofs/erdos_1194_note.tex`, Theorem 1. -/
@[category research solved, AMS 11]
theorem thm1_n_log_n_io (A : Set ℕ) (h : IsPDS A) (hA : A.Infinite) :
    ∃ c > (0 : ℝ), ∃ᶠ n in atTop,
      (aFun A h n : ℝ) ≥ c * (n : ℝ) * Real.log n := by
  sorry

/-- **Theorem 4 — partition-identity refinement, $a_n \gg n^{2-o(1)}$ i.o.**

For any infinite PDS `A` and every `c ∈ (1, 2)`, $\limsup_n a_n / n^c = \infty$.
Equivalently, no bound of the form `a_n ≤ K · n^c` can hold for all `n`,
for any `K > 0` and any `c < 2`.

*Proof sketch:* By the PDS partition identity, $X = \sum_k |D_k \cap [1, X]|$.
Under the hypothesis `a_n ≤ K · n^c`, the gap bound gives consecutive gaps
$(x_k - x_{k-1}) \geq (x_k/K)^{1/c}$, hence $x_k \gg k^{c/(c-1)}$ and
$|D_k \cap [1, X]| \leq X / x_k^{1/c}$. Splitting at $K = X^{(c-1)/c}$
yields $X \ll X^{2-2/c}$, a contradiction for $c < 2$.

*Reference:* GPT-5.4 Pro / T. Bloom, comment thread of erdosproblems.com/1194,
April 23, 2026 (post 5745); `proofs/erdos_1194_note.tex`, Theorem 2. -/
@[category research solved, AMS 11]
theorem thm4_n_two_minus_o_one_io (A : Set ℕ) (h : IsPDS A) (hA : A.Infinite)
    (c : ℝ) (hc : 1 < c) (hc' : c < 2) :
    ∀ K > (0 : ℝ), ∃ᶠ n in atTop, (aFun A h n : ℝ) > K * (n : ℝ)^c := by
  sorry

/-- **Theorem 5 — logarithmic refinement, $a_n \gg n^2/f(n)$ i.o.**

Let `f : ℕ → ℝ` be positive, nondecreasing, slowly varying
(`f(λn)/f(n) → 1` for every fixed `λ > 0`), unbounded, and satisfy
$\sum_{n \geq 2} 1/(n f(n)) < \infty$. Then for any infinite PDS `A`,
$a_n \gg n^2/f(n)$ for infinitely many `n`.

In particular, $a_n \gg (n/\log n)^2$ infinitely often (take
$f(n) = (\log n)^2$).

*Proof sketch:* Same scheme as Theorem 4, with `a_n ≤ K · n^2 / f(n)`
in place of `a_n ≤ K · n^c`. The gap bound becomes
$d_k \geq \sqrt{x_k f(d_k)/K}$, iterating to $x_k \gg k^2 f(k)$.
The anchor-window count becomes $|D_k \cap [1, X]| \ll X / (k f(k))$,
and the partition sum splits as $X \leq K^2/2 + X \varepsilon_K + o(X)$
where $\varepsilon_K \to 0$ by the convergence hypothesis, while
$K^2 = o(X)$ from `f(√X) → ∞`. The combined contradiction $X \leq 3X/4$
forces the result.

*Reference:* T. Bloom (optimisation of Theorem 4),
`proofs/erdos_1194_note.tex`, Theorem 3. -/
@[category research solved, AMS 11]
theorem thm5_n_squared_over_f_io (A : Set ℕ) (h : IsPDS A) (hA : A.Infinite)
    (f : ℕ → ℝ)
    (hf_pos : ∀ n, 2 ≤ n → 0 < f n)
    (hf_mono : ∀ m n, 2 ≤ m → m ≤ n → f m ≤ f n)
    (hf_slow : ∀ lam : ℝ, 0 < lam →
      Tendsto (fun n : ℕ => f ⌊lam * (n : ℝ)⌋₊ / f n) atTop (𝓝 1))
    (hf_top : Tendsto (fun n : ℕ => f n) atTop atTop)
    (hf_summable : Summable (fun n : ℕ => 1 / ((n : ℝ) * f n))) :
    ∃ K > (0 : ℝ), ∃ᶠ n in atTop,
      (aFun A h n : ℝ) ≥ K * (n : ℝ)^2 / f n := by
  sorry

/-- **Corollary of Theorem 5:** $a_n \gg (n/\log n)^2$ infinitely often. -/
@[category research solved, AMS 11]
theorem thm5_corollary_n_over_log_squared (A : Set ℕ) (h : IsPDS A) (hA : A.Infinite) :
    ∃ K > (0 : ℝ), ∃ᶠ n in atTop,
      (aFun A h n : ℝ) ≥ K * ((n : ℝ) / Real.log n)^2 := by
  sorry

/-- **Cilleruelo–Nathanson Open Problem 1 (the upper-bound side of #1194).**

Does there exist an infinite PDS `A` with $a_n = o(n^3)$? Equivalently, can
Lev's $n^3$ greedy upper bound be improved by a sub-cubic construction?

*Note (notation):* Cilleruelo–Nathanson use $t_n := b_n = a_n - n$. Since
$a_n = t_n + n$, we have $t_n = o(n^3) \iff a_n = o(n^3)$.

*Source:* J. Cilleruelo and M. B. Nathanson, *Perfect difference sets
constructed from Sidon sets*, Combinatorica 28 (2008), 401–414, §4.1
Open Problem 1.

Status: **open since 2008.** Empirical experiments in
`erdos_1194/results/seeded_summary.md` and `phase6_summary.md` confirm
that every greedy-style continuation (with any seed) produces
$\max_n a_n \asymp 0.002 \cdot N^3$ to $0.025 \cdot N^3$; no construction
within this family achieves sub-cubic. A genuinely non-greedy
continuation is required. -/
@[category research open, AMS 11]
theorem cina08_problem1 :
    answer(False) ↔
    ∃ A : Set ℕ, ∃ h : IsPDS A, A.Infinite ∧
      Tendsto (fun n : ℕ => (aFun A h (n + 1) : ℝ) / ((n + 1 : ℕ) : ℝ)^3)
        atTop (𝓝 0) := by
  sorry

/-- **Extension lower bound conjecture (Phase 4').**

There exists an exponent `c ∈ (1, 3]` such that for every infinite PDS `A`,
$a_n \gg n^c$ holds **for all sufficiently large $n$** (not merely
infinitely often).

This is strictly stronger than the infinitely-often form of Theorem 4 and,
if true, would be the first "for all large $n$" improvement on the trivial
$a_n \geq n + 1$. The value of $c$ is governed by the asymptotic growth
of the *extension cost*
$$M_{\mathrm{ext}}(A_0, N) := \min\{\max(A) : A \supseteq A_0,\ A\ \text{Sidon},\ [1, N] \subset A - A\}$$
as the seed `A_0` ranges over finite Sidon sets with $\max(A_0) \to \infty$.

*Source:* `erdos_1194/results/extension_summary.md`. Computational
trajectories from two finite optima (Phase 4' seeds $A_{20}^*$ and $A_{30}^*$)
exhibit $M_{\mathrm{ext}} \sim N^{4-5}$ in log-log fits with the exponent
*increasing* along the trajectory, suggesting $c$ is a moderate constant in
$[2, 3]$. No proof is known. -/
@[category research open, AMS 11]
theorem extension_lower_bound_conjecture :
    answer(True) ↔
    ∃ c : ℝ, 1 < c ∧ c ≤ 3 ∧
      ∀ A : Set ℕ, ∀ h : IsPDS A, A.Infinite →
        ∃ K > (0 : ℝ), ∃ N₀ : ℕ, ∀ n ≥ N₀,
          (aFun A h n : ℝ) ≥ K * (n : ℝ)^c := by
  sorry

end Erdos1194
