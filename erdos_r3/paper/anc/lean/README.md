# `r_3(212)` T1c Lean benchmark

Lean 4 / Mathlib 4 formalization of the audited T1c hard core from the
campaign described in `WRITEUP_DRAFT.md`. Released as a proof-search
benchmark target alongside the JSONL solver instances.

## Files

```
R3Base.lean              shared definitions: isAP3Free, R3DecisionProblem,
                         ChunkProblem, answer marker
R3_212_Witness.lean      verified 43-element 3-AP-free witness for [1, 212]
                         (discharges r_3(212) ≥ 43 via Finset.decide)
R3_T1c_40959.lean        T1c chunk 40959 statement (sorry; expected: false)
R3_T1c_48895.lean        T1c chunk 48895 statement (sorry; expected: false)
```

## Problem statement

Each T1c file states `target_theorem_0`: an equivalence between the
agent-supplied `answer(...)` value and a `ChunkProblem` instance. Closing
the chunk amounts to either

  * Supplying `false` for the EVOLVE-VALUE block and proving
    `¬ ChunkProblem 212 44 fixedIn fixedOut` (the expected branch), or
  * Supplying `true` and exhibiting an explicit 44-element 3-AP-free subset
    satisfying the pin constraints (which would disprove `r_3(212) ≤ 43`).

The expected answer per chunk is `false`, on the strength of:

  * `45`-chunk `300`-s CP-SAT recap returning `0 / 45` FEASIBLE
  * `8`-hour HiGHS MIP audit returning `0 / 45` FEASIBLE
  * `4`-hour pure CDCL/SAT returning `0 / 20` FEASIBLE on the LP-paradigm
    subset of T1, of which T1c is the residual
  * `12`-hour pure CDCL on T1c specifically returning UNKNOWN, not FEASIBLE
  * `4`-hour windowed CDCL on T1c returning UNKNOWN, not FEASIBLE

No machine-checkable infeasibility proof exists. Closing T1c here is the
campaign's open problem.

## Pin data provenance

The `fixedIn` / `fixedOut` sets in each chunk file come from
`results/N212_K44_broad24_recap300_residual_t1b20.jsonl`, which is the
filtered output of `extract_t1b_residual20.py`. The two T1c chunks differ
only in swapping which of `{27, 57}` is pinned IN vs OUT — they are
single-bit-flip neighbors in the depth-`24` broad-split chunk-ID space.

## Lean / Mathlib version

These files target Lean 4 with Mathlib 4 as of mid-2026. They use only
`Finset.Basic`, `Finset.Card`, `Order.LocallyFinite`, and `Mathlib.Tactic`;
no project-specific dependencies. They are intended to drop into a fresh
Lean project (`lake new R3 math`) without modification.

## How to attempt

### With AlphaProof Nexus or comparable LLM-based proof-search

Use each T1c file as the input "proof sketch". The EVOLVE-BLOCK / EVOLVE-
VALUE markers follow the convention of [Tsoukalas et al., arXiv:2605.22763].
The agent must:

  1. Replace `default` in the EVOLVE-VALUE block with `true` or `false`.
  2. Replace `sorry` in the EVOLVE-BLOCK with a discharging proof.

### Manual / human

`R3_212_Witness.lean` is a working example of how to close a feasibility
direction (the `r_3(212) ≥ 43` lower bound) by `decide` after expanding the
`Finset` literal. The T1c infeasibility direction requires more than
`decide` — the case analysis has roughly `binom(186, 33) ≈ 2.2e35` cases
after fixing the 26 chunk pins and 2 endpoints, so structural arguments
(window-cardinality, conflict-graph maximum independent sets,
density-increment) will be necessary.

## Relation to formal-conjectures

As of `2026-05-25`, the public
[google-deepmind/formal-conjectures](https://github.com/google-deepmind/formal-conjectures)
repository's OEIS listing did not contain an A003002 / `r_3(N)`
formalization. The files here are intended as a starting point: they could
be upstreamed to that repo as a new `OEIS/A003002` entry, with T1c as the
concrete fixed-`N` decision problem the agent should attempt.

## Sanity check

The convenience script `verify_lean_sanity.sh` creates a temporary
`lake new R3 math` project, copies these files into the `R3/` module tree,
and times the four checks:

```bash
bash verify_lean_sanity.sh

# Optional, if Mathlib cache is not already available:
R3_LEAN_CACHE_GET=1 bash verify_lean_sanity.sh
```

Manual equivalent inside a Lake project:

```bash
lake env lean R3Base.lean R3_212_Witness.lean
# expected: no errors; the witness theorems compile by `decide`.

lake env lean R3_T1c_40959.lean R3_T1c_48895.lean
# expected: a single `sorry` warning per file, on target_theorem_0.
```

The witness file's `A_43_isAP3Free` proof by `decide` may take a few
seconds (it ranges over `43³ ≈ 80k` ordered triples); if too slow,
replace with a `by simp` / explicit-cases proof or with a custom decision
procedure over `a < b < c`.
