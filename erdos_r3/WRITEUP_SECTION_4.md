# 4. The structural hard pocket

The headline empirical finding of the campaign is not the absence of a 44-element
3-AP-free subset of `[1, 212]` — which we expected from the OEIS A003002
extrapolation `r_3(212) = 43` — but the existence of a small, robust subset of
broad subproblems that resist every solver paradigm and search lever we threw
at them. We refer to this subset as the *hard pocket*. This section
characterizes it empirically, summarizes the unsuccessful interventions, and
states the resulting open problem.

## 4.1 Empirical signature on the broad population

The `100,000`-chunk window-bound broad batch over chunk-id range
`[11575, 111575)` produced `93,929` `INFEASIBLE` chunks, `6,071` `UNKNOWN`
chunks, and `0` `FEASIBLE` chunks under a `60`-second per-chunk wall cap. The
`6.07%` UNKNOWN rate is non-uniform in two distinct senses.

**Bucket non-uniformity.** Partitioned into twenty `5,000`-chunk buckets, the
UNKNOWN rate varies from `1.64%` to `13.60%`, with the worst bucket
`[61575, 66575)` at `13.60%`. The longest contiguous UNKNOWN run found in this
batch was length `27` at chunk IDs `98277..98303`; many other runs have length
around `15`. These contiguous runs are a strong indication that UNKNOWN status
is driven by joint structural properties of the depth-`24` witness-pin
assignment, not by stochastic solver behavior.

**Pin-OUT enrichment.** For each of the `24` broad-split witness variables we
computed the conditional UNKNOWN rate given that variable's IN/OUT assignment
in the chunk. Five variables — values `68`, `75`, `70`, `76`, `91`, all in the
dense middle cluster `[67, 91]` of the verified `43`-witness — show a strong
asymmetry: their conditional UNKNOWN rate is roughly `2.4%` when pinned IN
and `9.7%` when pinned OUT (Fisher log-odds `+3.5`). The signal is consistent
across the five values. We refer to a chunk in which all five hot pins are
forced OUT as a *middle-out chunk*. Middle-out chunks account for a
disproportionate share of the UNKNOWN tail of the broad batch.

## 4.2 The 300s-resistant tail does not collapse

To test whether the broad-pass UNKNOWNs were merely "slow" rather than
structurally hard, we ran two wall-cap recalibration experiments on a uniform
random sample of `100` UNKNOWN chunks drawn from the `6,071` baseline. The
results show a saturating, not exponential, closure curve:

| Wall cap | INFEASIBLE | UNKNOWN | Close rate over baseline |
|---:|---:|---:|---:|
| 60 s | 0 | 100 | 0% |
| 120 s | 31 | 69 | 31% |
| 300 s | 55 | 45 | 55% |

Going from `60s` to `120s` (2x) closed `31` chunks. Going from `120s` to
`300s` (2.5x further) closed only `24` more. Naïve extrapolation to `600s`
predicts perhaps `10`–`15` additional closures. The hard tail does not vanish
under more time.

We applied the same structural mining procedure (single-pin, pair, and triple
log-odds enrichment relative to a matched `INFEASIBLE` sample) to the `45`
`UNKNOWN` chunks that survived the `300s` cap. The broad pin-OUT signature
weakens substantially. The best high-coverage pair, `[91=OUT, 48=OUT]`, covers
`66.67%` of the survivors with log-odds `+1.226` — a modest effect size, far
from the `+3.5` signal seen on the `6,071`-row population. Top triples have
stronger log-odds but each covers only a handful of cases. Hamming-distance
clustering of survivor `fixed_in` sets shows multiple small clusters rather
than a single dominant niche. We interpret this as evidence that the
`300s`-resistant subproblems share moderate pin-OUT structure but spread
across many distinct sub-pockets of the depth-`24` assignment lattice.

## 4.3 LP-paradigm failure and the CDCL break

The 300s-resistant pocket might in principle be a CP-SAT-specific
phenomenon — an artifact of constraint propagation's inability to exploit
implicit LP structure. To test this, we re-attacked all `45` survivors with
the HiGHS open-source MIP solver \cite{huangfu-hall-2018-highs}, which combines branch-and-bound, LP
relaxation, presolve, cutting planes, and primal heuristics. We used a
one-hour wall cap per chunk, `8` threads per chunk, and the identical
constraint set
(decision-form `sum x_i = 44`, all `11,130` 3-AP triple inequalities, all
`22,154` window-cardinality inequalities, plus the broad chunk's `fixed_in`
and `fixed_out` assignments tightened into variable bounds).

The one-hour result was negative:

The two rows in the following table are not a common-sample comparison: the
HiGHS attack targets precisely the `45` chunks that survived the `300`-s
CP-SAT recap, i.e. the harder subset of the `100` recap inputs.

| Solver | Constraints | Wall cap | Closed (INF) | UNKNOWN | Aggregate solver wall time |
|---|---:|---:|---:|---:|---:|
| CP-SAT, window-bounds | 3-AP + window + symmetry | 300 s | 55 / 100 | 45 / 100 | bounded by ~8.3 wall-h |
| HiGHS, window-bounds | 3-AP + window + endpoint | 3,600 s | **0 / 45** | 45 / 45 | 45.0 wall-h |

Across `162,003` solver-seconds and `3,181,316` explored MIP nodes, HiGHS did
not close a single chunk. No `FEASIBLE` row appeared. The recorded HiGHS dual
bound stayed at its uninformative default value in every task, which is itself
evidence that the LP-relaxation route was not discovering a useful certificate
for these instances.

We then re-attacked all `45` T1 chunks under an extended `8`-hour HiGHS wall,
with LP progress logging enabled. The result is mixed: `25 / 45` chunks closed
`INFEASIBLE`, while `20 / 45` returned `UNKNOWN` at the full cap with dual
bound still pinned at `0.0`. We call this `20`-chunk LP-paradigm-resistant
subset **T1b**. The audit consumed `901,073` solver-seconds and `25,196,448`
MIP nodes.

To test whether T1b is invariant under solver architecture more broadly, we
re-attacked it with a CDCL/SAT solver (CaDiCaL via PySAT
\cite{biere-cadical,pysat-2018}, single-threaded,
`4`-hour wall, encoding restricted to 3-AP triples + cardinality + chunk pins;
no window-cardinality clauses). CDCL closed `18 / 20` chunks `UNSAT`. We call
the surviving `2`-chunk residual **T1c** = `{40959, 48895}`. A T1c diagnostic
at extended wall (`12` h pure CDCL) and with totalizer-encoded window
constraints for lengths `{31, 100, 199}` (`4` h) also returned `UNKNOWN` on
both chunks, so T1c is resistant to all tested paradigms in this campaign.

A proof-producing rerun of the `18` CDCL-UNSAT chunks initially emitted DRAT
proofs for `17` chunks; the remaining chunk, `32735`, required a larger-memory
proof rerun and then also emitted a DRAT proof. Independent `drat-trim`
verification confirmed all `18 / 18` emitted proofs. The final two certificates
were the slowest: `63231` verified in `49,758.11` seconds and `32735` verified
in `80,960.68` seconds under the final `24`-hour verifier pass
\cite{heule-hunt-biere-drat-2014,cruz-filipe-lrat-2017}.

The refined paradigm-invariance picture is therefore: **LP-paradigm methods
(CP-SAT constraint propagation and HiGHS LP-relaxation MIP) fail uniformly on
T1b**, and the CDCL clause-learning paradigm closes `18 / 20` of those chunks,
all of which are independently verified. The genuinely paradigm-invariant
residual is T1c, of size `2`.

## 4.4 Levers tested and their outcomes

For completeness, we record every search-tuning lever we tested on the hard
bucket `[61575, 66575)` or the `300s`-resistant subset. The CP-SAT/MIP-side
tuning levers did not remove the hard pocket; the one qualitative exception is
the CDCL paradigm switch, which closes most of T1b and therefore narrows, rather
than merely tunes, the residual.

| Lever | Mechanism | Result |
|---|---|---|
| Window-cardinality (OEIS A003002) | Add `sum x ≤ r_3(L)` for each window | UNK rate on full `10k` batch: `30.33% → 1.65%`. Strong but plateaus. |
| Split-vars reorder (hot pins first) | Permute the depth-`24` split prefix | `13.60% → 12.96%` on the worst bucket. Noise. |
| Wall-cap extension | `60s → 300s` on the broad pass | Saturating curve, see §4.2. |
| Targeted pair-AND Tseitin propagators | Explicit `pair[a,c] = x[a]∧x[c]` BoolVars on midpoints in `[67, 91]` | Control `67.84s`, treatment `71.75s` on a sampled residual. No effect. |
| Recursive deepening | Refinement at depths `40`, `48`, `56` | All `500` stratified-sample base chunks close, but with a non-trivial tail; the final six level-3 residuals needed up to `599.74s` at the `600s` cap. |
| HiGHS MIP with LP/cut machinery | Replace CP-SAT entirely | `0 / 45` closed at `1` hour; `25 / 45` closed in the full `8`-hour audit, while `20 / 45` retained dual bound `0.0`. |
| Pure CDCL/SAT | Encode T1b as CNF with 3-AP clauses + cardinality + pins, no windows | `18 / 20` HiGHS-flat chunks closed `UNSAT` in 4 hours; `2 / 20` remained `UNKNOWN`; no `SAT` rows. This breaks the strong solver-invariance framing. |

The pair-AND result is worth a closer note. The added constraints are
mathematically redundant with the existing 3-AP triple inequalities — they
encode the same forbidden configurations, just with an explicit Tseitin
variable per pair. The hope was that this would give CP-SAT more
"propagation hooks" in the structural pocket. The negative result is
consistent with the broader picture: the pocket's hardness is not an
encoding issue, it is a search-space issue.

## 4.5 A conjecture about the pocket

We end §4 with a working conjecture about T1c.

CDCL closed `18 / 20` of T1b, refuting the strongest reading of
solver-paradigm invariance for the full `20`-chunk LP-flat subset. The
conjecture below is deliberately narrower: it concerns only the two chunks
that survived the CDCL break.

Each T1c subproblem corresponds to a depth-`24` fixed assignment in which
`(i)` the LP relaxation upper bound on `sum x_i` is at most one above the
decision threshold `K = 44`, leaving no room for LP-based cuts to prove
infeasibility, and `(ii)` the integer infeasibility certificate is too
combinatorially diffuse to fit in the working memory of current CDCL
clause-learning solvers under a `12`-hour wall. The audit of §4.3 bounds the
T1c population at `2` chunks within the `100,000`-chunk window-bound expansion
residual; we do not have a population-level estimate beyond the audited
region.

If this picture is correct, closing T1c requires either (a) a
problem-specific additive-combinatorial upper bound tighter than the OEIS
window-cardinality family, or (b) a custom branch-and-bound or proof-search
system that exploits problem structure neither current general-purpose solver
paradigm captures. Both are framed as open computational problems in §5.

## 4.6 What this means for `r_3(212)`

The combined CP-SAT, HiGHS, and CDCL evidence — `0` `FEASIBLE`/`SAT` rows
across millions of subproblems and all audited hard-pocket diagnostics —
strongly supports the OEIS-conjectured value `r_3(212) = 43`, but the
surviving T1c pocket means we do not have a formal proof of the upper bound
`r_3(212) ≤ 43`. The `6,071` baseline UNKNOWN chunks (and the much larger
unobserved tail of the full `12,582,912`-chunk depth-`24` sweep) remain an
open obstruction. The lower bound `r_3(212) ≥ 43` from the verified witness in
§2 is unaffected. The trivial upper bound `r_3(212) ≤ 44` follows from
monotonicity and OEIS `r_3(211) = 43`, so the gap between our certified bounds
is exactly one.

Closing that final unit gap would require resolving T1c and independently
certifying the entire depth-`24` sweep, including the unprocessed remainder of
the `12,582,912`-chunk T3 lattice. T1c is the sharpest audited open instance,
not necessarily a sufficient stepping stone. We release the hard-pocket
benchmark instances in §5 so specialists can attempt this directly.
