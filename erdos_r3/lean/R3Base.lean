/-
R3Base.lean

Common Lean 4 / Mathlib 4 definitions for the r_3(N) frontier-computation
benchmark accompanying the writeup "Witness-split + window-cardinality
refinement for r_3(N)" (Ergezer et al., 2026).

The file defines:
  * isAP3Free : Finset ℕ → Prop, the standard "no nontrivial 3-AP" predicate
  * R3DecisionProblem N K, the existence question
  * ChunkProblem N K fixedIn fixedOut, the per-chunk fixed-assignment version
  * answer : Bool → Prop, a marker compatible with AlphaProof Nexus-style
    EVOLVE-BLOCK problem files

The chunk problem is the unit the §5 benchmark release distributes one row
per chunk. The unit-gap target is r_3(212) ∈ {43, 44}, equivalently the
existence question with N = 212, K = 44.

Verified lower bound: see R3_212_Witness.lean for the 43-element witness and
its 3-AP-free proof (discharges r_3(212) ≥ 43).

Open: chunks 40959 and 48895 of the depth-24 broad split are the audited
"T1c" hard core; their Lean statements are in R3_T1c_40959.lean and
R3_T1c_48895.lean. Both are believed (with strong empirical evidence) to be
infeasible, so the expected answer is False in each case, but neither has a
machine-verifiable proof in this campaign.
-/

import Mathlib.Data.Finset.Basic
import Mathlib.Data.Finset.Card
import Mathlib.Order.LocallyFinite
import Mathlib.Tactic

namespace R3

/-- A subset of ℕ is 3-AP-free iff it contains no three distinct elements in
arithmetic progression. The standard formulation is: no `a < b < c` in `A`
satisfy `a + c = 2 * b`. -/
def isAP3Free (A : Finset ℕ) : Prop :=
  ∀ a b c, a ∈ A → b ∈ A → c ∈ A → a < b → b < c → a + c ≠ 2 * b

/-- The standard "r_3(N)" decision problem at threshold K: does there exist a
K-element 3-AP-free subset of [1, N]? -/
def R3DecisionProblem (N K : ℕ) : Prop :=
  ∃ A : Finset ℕ, A ⊆ Finset.Icc 1 N ∧ A.card = K ∧ isAP3Free A

/-- Per-chunk decision problem with fixed-in / fixed-out pins. A chunk is
feasible iff there exists a K-element 3-AP-free subset of [1, N] that
contains every element of `fixedIn` and avoids every element of `fixedOut`.
-/
def ChunkProblem
    (N K : ℕ) (fixedIn fixedOut : Finset ℕ) : Prop :=
  ∃ A : Finset ℕ,
    A ⊆ Finset.Icc 1 N ∧
    A.card = K ∧
    isAP3Free A ∧
    fixedIn ⊆ A ∧
    Disjoint A fixedOut

/-- `answer` marker used in AlphaProof Nexus-style EVOLVE-VALUE blocks. The
problem statement is phrased as `answer(...) ↔ <math statement>`; the agent
fills the EVOLVE-VALUE block with `True` or `False` (a guess at the answer)
and discharges the equivalence. -/
def answer (b : Bool) : Prop := b = true

@[simp] lemma answer_true : answer true ↔ True := by
  unfold answer; simp

@[simp] lemma answer_false : answer false ↔ False := by
  unfold answer; simp

/-- Sanity-check direction: if the chunk problem is infeasible, the answer
marker should evaluate to False. -/
lemma chunk_infeasible_iff_answer_false
    (N K : ℕ) (fixedIn fixedOut : Finset ℕ)
    (h : ¬ ChunkProblem N K fixedIn fixedOut) :
    answer false ↔ ChunkProblem N K fixedIn fixedOut := by
  rw [answer_false]; tauto

/-- Sanity-check direction: if the chunk problem is feasible, the answer
marker should evaluate to True. -/
lemma chunk_feasible_iff_answer_true
    (N K : ℕ) (fixedIn fixedOut : Finset ℕ)
    (h : ChunkProblem N K fixedIn fixedOut) :
    answer true ↔ ChunkProblem N K fixedIn fixedOut := by
  rw [answer_true]; tauto

end R3
