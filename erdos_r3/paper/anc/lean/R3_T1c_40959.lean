/-
R3_T1c_40959.lean

T1c benchmark chunk 40959 of the depth-24 broad split for `r_3(212) ≤ 43`.

This chunk is one of two surviving the campaign's full four-paradigm
attack (CP-SAT propagation, HiGHS LP-MIP at 8h, pure CDCL at 12h, and
CDCL with windowed cardinality at 4h). It is released as a formal-proof-
search benchmark target.

The structure follows AlphaProof Nexus-style EVOLVE-BLOCK conventions:
the agent fills in the EVOLVE-VALUE block with `true` or `false`
(its guess at the answer) and supplies a proof of the resulting
equivalence inside the EVOLVE-BLOCK.

Expected answer: `false`. The CDCL hard-pocket diagnosis suggests the
chunk is infeasible (i.e., no 44-element 3-AP-free subset of [1, 212]
exists with the given fixed-in / fixed-out pins), but no machine-
checkable proof was produced by this campaign.

Provenance: results/N212_K44_broad24_recap300_residual_t1b20.jsonl,
chunk_id = 40959.
-/

import Mathlib.Data.Finset.Basic
import Mathlib.Tactic

import «R3».R3Base

namespace R3.T1c_40959

open R3

/-- Fixed-IN pins for chunk 40959: 11 elements including the forced
endpoints 1 and 212. -/
def fixedIn : Finset ℕ :=
  ({1, 3, 4, 9, 11, 12, 16, 22, 25, 27, 212} : Finset ℕ)

/-- Fixed-OUT pins for chunk 40959: 15 elements including the middle-out
signature {67, 68, 70, 75, 76, 91} that characterizes the campaign's hard
pocket. -/
def fixedOut : Finset ℕ :=
  ({24, 31, 48, 52, 54, 55, 57, 63, 67, 68, 70, 75, 76, 91, 142} : Finset ℕ)

/-- The chunk decision problem: does a 44-element 3-AP-free subset of
[1, 212] exist that contains every element of fixedIn and avoids every
element of fixedOut? -/
abbrev problem : Prop := ChunkProblem 212 44 fixedIn fixedOut

-- EVOLVE-BLOCK-START
-- The agent may introduce helper lemmas / definitions / proof steps here.
-- EVOLVE-BLOCK-END

theorem target_theorem_0 :
    answer (
      -- EVOLVE-VALUE-START
      default
      -- EVOLVE-VALUE-END
    ) ↔ problem := by
  -- EVOLVE-BLOCK-START
  sorry
  -- EVOLVE-BLOCK-END

end R3.T1c_40959
