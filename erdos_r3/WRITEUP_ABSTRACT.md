We describe a reproducible computational framework for upper-bound searches on
`r_3(N)`, the maximum size of a 3-term-arithmetic-progression-free subset of
`[1, N]`. The framework combines a verified lower-bound witness, endpoint
forcing, depth-`d` witness-variable splitting, OEIS A003002 window-cardinality
pruning, and recursive refinement of timed-out subproblems. Applied to the
frontier case `N = 212, K = 44`, it found no feasible `44`-set across millions
of CP-SAT subproblems, supporting but not proving the conjectural value
`r_3(212) = 43`. The main technical findings concern the structural hard
pocket of the residual. A `300`-second recap leaves `45` resistant chunks;
one-hour HiGHS MIP closes none of them; the full eight-hour HiGHS audit
closes `25 / 45` and leaves `20 / 45` with dual bounds still pinned at `0.0`.
A CDCL/SAT re-attack on those `20` LP-paradigm-resistant chunks closes `18`
via conflict-driven clause learning, all of which carry independently
verified DRAT proofs; the remaining `2` chunks (`T1c`) resist all tested
paradigms -- CP-SAT propagation, HiGHS LP-MIP, pure CDCL, and CDCL with a
small window-cardinality subset -- under generous wall caps. We release the
witness, solver scripts, result logs, tiered benchmark instances
(`T1a`, `T1b minus T1c`, `T1c`), the verified DRAT proofs, and a Lean
formal-proof-search encoding of `T1c`, and frame the unit-gap problem
`r_3(212) in {43, 44}` as a target for stronger additive-combinatorial bounds,
custom branch-and-bound, or formal proof-search systems.
