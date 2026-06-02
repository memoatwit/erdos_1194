/-
R3_212_Witness.lean

The verified 43-element 3-AP-free subset of [1, 212] from
`results/N212_K43_witness.json`. This file states the lower bound
`r_3(212) ≥ 43` as an explicit existence claim and leaves the
3-AP-free proof as a finite case-check that any Lean automation
(or a proof-search agent) should be able to discharge by enumeration.

The witness was independently verified by `r3_verify.py` against a
triple-enumeration check; the Lean statement below should evaluate to
the same conclusion.
-/

import Mathlib.Data.Finset.Basic
import Mathlib.Tactic

import «R3».R3Base

namespace R3

/-- The verified 43-element 3-AP-free subset of [1, 212]. -/
def A_43 : Finset ℕ :=
  ({3, 4, 9, 11, 12, 16, 22, 24, 25, 27, 31, 48, 52, 54, 55, 57, 63, 67,
    68, 70, 75, 76, 91, 142, 145, 150, 152, 156, 161, 164, 165, 168, 181,
    182, 187, 189, 190, 195, 202, 204, 205, 207, 211} : Finset ℕ)

/-- Cardinality of the witness is 43. Should be discharged by `decide` once
the Finset literal expands. -/
theorem A_43_card : A_43.card = 43 := by
  unfold A_43; decide

/-- The witness lives inside [1, 212]. Should be discharged by `decide`. -/
theorem A_43_subset : A_43 ⊆ Finset.Icc 1 212 := by
  unfold A_43; decide

/-- The witness is 3-AP-free. This is a finite case check over the
`43 * 43 * 43 = 79,507` ordered triples; `decide` should discharge it,
albeit not instantaneously. A faster route is a custom decision procedure
that ranges only over `a < b < c`, but the brute-force statement is more
transparent. -/
theorem A_43_isAP3Free : isAP3Free A_43 := by
  unfold isAP3Free A_43
  decide

/-- Lower bound r_3(212) ≥ 43, packaged as a witness for `R3DecisionProblem`. -/
theorem r3_212_lower_bound : R3DecisionProblem 212 43 := by
  refine ⟨A_43, ?_, ?_, ?_⟩
  · exact A_43_subset
  · exact A_43_card
  · exact A_43_isAP3Free

end R3
