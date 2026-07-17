# 5. Open problem and benchmark release

The campaign establishes strong empirical support for `r_3(212) = 43`
(§3.4) but leaves a hard pocket that resists both CP-SAT and HiGHS
under every lever we tested (§4). To turn that pocket into a tractable
research target rather than an open compute frontier, this section
states the residual problem cleanly and releases the surviving
instances as a tiered benchmark.

## 5.1 Statement of the open problem

> **Problem (R3-212-UB).** Let `A ⊆ [1, 212]` with `|A| = 44`. Determine
> whether there exists `A` containing no nontrivial 3-term arithmetic
> progression. The verified `43`-element witness in
> `results/N212_K43_witness.json` (§2.1) and the value `r_3(211) = 43`
> from OEIS A003002 jointly imply that any such `A` must contain both
> endpoints `1` and `212`. Equivalently, either exhibit one such `A`
> or certify the infeasibility of the decision problem
> `sum_i x_i = 44` over the `3`-AP constraint family on `[1, 212]`
> with `x_1 = x_{212} = 1`.

A solution to R3-212-UB resolves the unit gap `r_3(212) ∈ \{43, 44\}`
in either direction. Our multi-million-subproblem CP-SAT campaign and
the `45`-instance HiGHS attack returned `0` `FEASIBLE` rows, which is
evidence for the infeasibility branch but not a proof. The
benchmark instances released below pinpoint the subproblems on which
generic combinatorial-optimization solvers currently fail.

## 5.2 Benchmark instance tiers

We release three tiered benchmark sets. Each JSONL row records the chunk ID,
fixed assignments, witness-pin prefix, solver status, and timing data; the
common constraint family (3-AP triples, endpoint forcing, and OEIS window
bounds) is reconstructed by the repository scripts. The tiers form a ladder
from the smallest solver-resistant pocket to the full upper-bound proof.

| Tier | Artifact | Size | Resistance level | Recommended target |
|---|---|---:|---|---|
| T1a | T1a JSONL | `25` chunks | closed by HiGHS at `8`h (dual = `inf`) | reference / regression test |
| T1b ∖ T1c | T1b-minus-T1c JSONL | `18` chunks | LP-paradigm-resistant; closed by CDCL; all `18 / 18` emitted DRAT proofs verified by `drat-trim` | certified CDCL benchmark |
| T1c | T1c JSONL | `2` chunks | resistant to CP-SAT, HiGHS LP-MIP, pure CDCL @ `12`h, and windowed CDCL @ `4`h | minimum-viable proof step |
| T2 | T2 JSONL | `6,071` chunks | survived `60`-s CP-SAT broad pass with window bounds | full closure of the expansion residual |
| T3 | deterministic generator | `12,582,912` chunks | unprocessed remainder of the witness-split lattice | full upper-bound proof |

The concrete filenames are \path{results/N212_K44_t1a25.jsonl},
\path{results/N212_K44_t1b_minus_t1c.jsonl},
\path{results/N212_K44_t1c2.jsonl}, and
\path{results/N212_K44_window100k_unknowns.jsonl}.

Tier T1c is the campaign's sharpest open problem: `2` chunks resistant to
every tested solver paradigm under generous wall caps. A successful T1c closure
either disproves `r_3(212) ≤ 43` (one `FEASIBLE`/`SAT` row suffices, after
witness verification) or eliminates the audited four-paradigm-resistant
residual, leaving the unit gap depending on the unprocessed remainder of T3.

Tier T2 is the canonical "close the campaign at the broad layer"
target: closing all `6,071` chunks of the `100k` expansion batch is
necessary, though not sufficient, for a full upper-bound proof.

Tier T3 is the full upper-bound certificate: closing the entire
depth-`24` AP-pruned sweep. The instance generator (§2.2) emits the
required chunks deterministically from the witness file and the
OEIS b-file; the storage cost of the full sweep is dominated by
output rather than input.

## 5.3 Minimum-viable proof requirements

A formal proof of `r_3(212) ≤ 43` from the released benchmark requires:

1. **Closure of tier T3.** Every chunk in the depth-`24` AP-pruned
   sweep must return `INFEASIBLE` under a verified solver, or one
   chunk must return a `FEASIBLE` `44`-element witness.
2. **Solver verification.** We recommend that any solver used for closure
   either produce machine-checkable proof certificates (DRAT, LRAT, or
   equivalent), or be independently reproduced under a second solver paradigm.
   This is a verification target rather than a condition already met by every
   row of the present campaign; §6.2 records the remaining certificate gaps.
3. **Constraint-set verification.** The `11,130` 3-AP triple
   inequalities, the `22,154` window-cardinality inequalities, and
   the endpoint forcing must be checked against the formal
   definition of `r_3(N)`. The verifier `r3_verify.py` performs
   this check on any candidate witness; an analogous check for the
   constraint generation is included in the repository.

The minimum-viable result short of a full proof is closure of T1c
under a solver paradigm that produces a usable bound certificate
(e.g., LP dual values that improve under cuts, or a CDCL-style
unsatisfiability proof on a SAT encoding of the same constraints).
This would establish that the hard pocket is not solver-architecture
invariant after all, contradicting the conjecture of §4.5.

## 5.4 Approaches we could not test

The following techniques are plausibly stronger than CP-SAT and HiGHS
on this pocket but were outside the scope of our campaign. We flag
them as natural follow-on directions:

- **Fourier-analytic upper bounds.** Behrend-style constructions
  achieve `r_3(N) = N · exp(-c·sqrt(log N))` lower bounds; a
  matching Fourier-analytic upper bound for small `N` would give a
  certificate independent of combinatorial search. The Bloom–Sisask
  framework for `r_3(N) = O(N / (log N)^{1+c})` is asymptotic but
  the underlying density-increment machinery may yield finite-`N`
  bounds tighter than the OEIS window-cardinality family.
- **Multi-window partition bounds.** OEIS A003002 is used here as
  a single-window family `sum_{[a, a+L)} x_i ≤ r_3(L)`. A
  partition-cardinality bound across multiple disjoint windows of
  varying length might cut the LP relaxation more aggressively
  than any single-window family.
- **SAT with proof logging.** A pure CNF encoding has already closed
  `18 / 20` T1b chunks using PySAT/CaDiCaL without OEIS window constraints.
  Follow-up proof-producing runs emitted DRAT proofs for all `18` CDCL-closed
  chunks, and `drat-trim` independently verified all `18 / 18`. The research
  target is now T1c: try longer CDCL walls, different cardinality encodings,
  full-window encodings, or native proof-producing SAT solvers on chunks
  `40959` and `48895`.
- **Lean/formal-proof-search benchmark.** The repository now includes a compact
  Lean 4 / Mathlib 4 formalization \cite{lean4-2021,mathlib4} under `lean/`: shared definitions
  (`R3Base.lean`), the verified `43`-witness statement
  (`R3_212_Witness.lean`), and two AlphaProof-style T1c targets
  (`R3_T1c_40959.lean`, `R3_T1c_48895.lean`) with the expected answer `false`.
  These files are intended as a starting point for an A003002 / `r_3(N)` entry
  in formal-conjecture repositories \cite{formal-conjectures}. Recent AlphaProof Nexus-style workflows
  have resolved Erdős problems of comparable complexity at low per-problem cost
  when a Lean target exists \cite{tsoukalas-alphaproof-nexus-2026}, so T1c is well-shaped for that paradigm.
- **Custom branch-and-bound.** A solver that exploits problem-
  specific symmetries and dominance relations — for instance,
  reflection symmetry after endpoint forcing, or domination of one
  window-bound by another at specific fixed-pin configurations —
  could prune branches that neither CP-SAT nor HiGHS recognize as
  redundant.
- **Symmetric Difference Encoding / Lasserre hierarchy at low
  degree.** A degree-`4` or degree-`6` SDP relaxation of the
  3-AP-free constraint might separate the surviving T1 instances
  from feasibility where the LP relaxation cannot.

We do not advocate for any single direction. The benchmark release
is intended to let specialists pick the technique closest to their
toolkit.

## 5.5 Reproducibility and release

The campaign code, configuration, and result logs are released at
the repository accompanying this preprint. Specifically:

- All Python sources implementing the architecture of §2 are present
  with module-level documentation.
- The SLURM scripts (`submit_*.sbatch`) and the driver
  `unity_handoff.sh` reproduce the full campaign on any
  SLURM-compatible cluster with OR-Tools and `highspy` installed.
- The verified `43`-witness, the OEIS A003002 b-file used for window
  bounds, the broad-pass result logs, the recap residuals, the
  HiGHS attack logs, the T1a/T1b/T1c benchmark JSONLs, verified DRAT
  certificates, LRAT artifacts where emitted with `drat-trim -L`, the Lean T1c
  proof-search targets, environment/version captures for the main solver stack,
  and the scripts needed to generate T3 are all included.
- Existing single-instance entry points (`r3_split_cpsat.py` and
  `r3_highs_attack.py`, and `r3_sat_attack.py`) can rerun any row of T1c,
  T1b, or T2 by chunk ID.

The large solver artifacts are archived on Zenodo at
<https://doi.org/10.5281/zenodo.21413746>. This archive contains the
CNF/DRAT proof artifacts for the `18` CDCL-closed T1b \ T1c chunks,
the available LRAT outputs, verification summaries, SLURM logs, solver
outputs, SHA256 manifests, and reconstruction instructions for split
archives \cite{ergezer-r3-212-artifacts-2026}.

We welcome correspondence on partial results: any solver run that
closes a strict subset of T1 or T2 is a meaningful incremental
contribution, even if the full upper bound remains open.
