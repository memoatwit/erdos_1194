# Post-CDCL Writeup Patch Kit

Date: 2026-05-26

This patch kit updates the writeup after Unity SAT/CDCL job `58832970`.

## Result Summary

Pure CDCL/SAT over the audited T1b hard core closed most of what CP-SAT and
HiGHS could not:

| Solver / run | Instance set | Encoding | Cap | Closed | Residual | Feasible |
|---|---:|---|---:|---:|---:|---:|
| HiGHS long-wall | T1 (`45`) | 3-AP + windows + bounds | 8 h | `25 / 45` | `20 / 45` | `0` |
| CDCL/SAT | T1b (`20`) | 3-AP + cardinality + pins only | 4 h | `18 / 20` | `2 / 20` | `0` |

Total recorded SAT-row time: `71,216.85474205017` seconds.

Residual T1c chunks: `40959`, `48895`.

Important certificate caveat: this first SAT run used `pysat:auto`
(`cadical195`) and did **not** emit DRAT/LRAT certificates. The result is a
strong cross-paradigm diagnostic, not yet a machine-checkable proof artifact.

## Replacement Abstract

```markdown
We describe a reproducible computational framework for upper-bound searches on
`r_3(N)`, the maximum size of a 3-term-arithmetic-progression-free subset of
`[1, N]`. The framework combines a verified lower-bound witness, endpoint
forcing, depth-`d` witness-variable splitting, OEIS A003002 window-cardinality
pruning, and recursive refinement of timed-out subproblems. Applied to the
frontier case `N = 212, K = 44`, it found no feasible 44-set across millions of
CP-SAT subproblems, supporting but not proving the conjectural value
`r_3(212) = 43`. The main technical finding is a solver-dependent hard pocket:
a 300-second CP-SAT recap leaves 45 resistant chunks; an eight-hour HiGHS MIP
audit closes `25/45` but leaves `20/45` with dual bounds pinned at `0.0`;
then a pure CDCL/SAT encoding, using only 3-AP clauses, cardinality, and chunk
pins, closes `18/20` of those HiGHS-flat chunks. The final audited hard core is
two chunks. We release the witness, solver scripts, result logs, and tiered
benchmark instances, and frame the remaining unit-gap problem as a target for
proof-logging SAT, additive-combinatorial bounds, custom branch-and-bound, or
formal proof-search systems.
```

## Section 4 Retitle

Replace:

```markdown
## 4.3 Solver-paradigm invariance: CP-SAT and HiGHS fail the same way
```

with:

```markdown
## 4.3 LP-paradigm failure and the CDCL break
```

## Section 4.3 Replacement Paragraph

Replace the final interpretive paragraph of §4.3 with:

```markdown
The full-T1 HiGHS audit established a sharp LP-paradigm failure, but not a
solver-paradigm-invariant hard pocket. We subsequently encoded the `20`
HiGHS-flat T1b chunks as pure CNF SAT instances using only the `11,130` 3-AP
clauses, cardinality `sum x_i = 44`, endpoint forcing, and chunk pins; the
OEIS window-cardinality constraints were deliberately omitted. A PySAT
`cadical195` backend closed `18 / 20` chunks `UNSAT` under a `4`-hour cap,
with `0` `SAT` rows and total recorded time `71,216.85` seconds. Only chunks
`40959` and `48895` remained `UNKNOWN`. Thus the hard pocket is not
solver-architecture invariant in the strong sense: CDCL learns short enough
propositional contradictions for most of the LP-flat core. The residual hard
core is now T1c, a two-chunk set that has resisted CP-SAT, long-wall HiGHS, and
4-hour pure CDCL/SAT.
```

## Section 4.4 Table Update

Add this row after the HiGHS row:

```markdown
| Pure CDCL/SAT | Encode T1b as CNF with 3-AP clauses + cardinality + pins, no windows | `18 / 20` HiGHS-flat chunks closed `UNSAT` in 4 hours; `2 / 20` remained `UNKNOWN`; no `SAT` rows. This breaks the strong solver-invariance framing. |
```

## Section 4.5 Conjecture Replacement

Replace the first paragraph of §4.5 with:

```markdown
The post-CDCL evidence changes the conjecture. The older hypothesis — that the
integer infeasibility certificates are too diffuse for any short solver proof —
is false for most of T1b: CDCL found moderate-length contradiction searches for
`18 / 20` chunks despite omitting all window bounds. What survives is a more
specific LP-relaxation claim: the window-bound MIP relaxation has essentially
zero proving power on the T1b rows whose HiGHS dual bound stays pinned at
`0.0`. The contradiction exists in the propositional 3-AP/cardinality
structure, but it is not visible to the LP/cut machinery used in HiGHS.
```

Then replace the final sentence of §4.5 with:

```markdown
The remaining question is whether the two T1c chunks are merely longer CDCL
instances or whether they require a qualitatively stronger encoding or proof
system.
```

## Section 5.2 Tier Table Replacement

Replace the T1 row with three rows:

```markdown
| T1 | `results/N212_K44_broad24_recap300_residual45.jsonl` | `45` chunks | survived `300`-s CP-SAT recap; HiGHS 8h audit closes `25 / 45` | minimum-viable cross-solver benchmark |
| T1b | `results/N212_K44_broad24_recap300_residual_t1b20.jsonl` | `20` chunks | HiGHS-flat after 8h with dual bound `0.0` | LP-paradigm hard core |
| T1c | extract rows `40959`, `48895` from T1b | `2` chunks | survived CP-SAT, 8h HiGHS, and 4h pure CDCL/SAT | current audited hard core |
```

## Section 5.4 SAT Bullet Replacement

Replace the SAT bullet with:

```markdown
- **SAT with proof logging.** A pure CNF encoding has already closed `18 / 20`
  T1b chunks using PySAT/CaDiCaL without OEIS window constraints. That run did
  not emit DRAT/LRAT certificates, so the natural next proof-engineering step
  is to rerun the `18` closed chunks with a proof-producing SAT backend and
  then attack the two T1c chunks (`40959`, `48895`) with either longer CDCL
  walls, window-constraint encodings, or a different cardinality encoding.
```

## Section 6.2 Limitation Update

Replace the no-certificates bullet with:

```markdown
- **No machine-checkable certificates yet.** Neither CP-SAT nor HiGHS emitted
  DRAT/LRAT-style certificates. The first SAT/CDCL run closed `18 / 20` T1b
  chunks but used the portable PySAT backend without proof output. A
  proof-logging rerun of those `18` rows would turn the strongest current
  diagnostic into independently checkable artifacts.
```

## Section 3.6 Budget Row

Add:

```markdown
| Pure CDCL/SAT on T1b | `~19.8` | `20` single-core tasks, retained JSON row time `71,216.85` seconds |
```

This is solver wall in core-hours because the SAT run used one thread per task.

