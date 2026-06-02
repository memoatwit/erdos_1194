# 3. Empirical campaign

This section reports the workload, results, and key A/B tests of the
`r_3(212) ≤ 43` campaign. All experiments were run on the UMass Unity
SLURM cluster against the architecture described in §2. The headline
numbers: millions of CP-SAT subproblems solved, `0` `FEASIBLE`
rows, and a `6.07%` `UNKNOWN` residual in the largest retained broad batch that
motivates the structural analysis in §4.

## 3.1 Chunk-count breakdown

The campaign proceeded in three layers of increasing scope, plus a
recursive-refinement loop on the `UNKNOWN` residuals.

**Verified lower bound.** A `43`-element 3-AP-free subset of `[1, 212]` is
recorded in the repository's witness JSON and re-verified by
`r3_verify.py` against an independent triple-enumeration check. This
witness fixes the campaign's `K = 44` decision-mode target and supplies
the seed for the depth-`24` broad split (§2.2).

**Broad pass at depth `24`, `60`-s wall.** The retained broad-pass logs include
both pre-window and window-bound runs:

| Range | Chunks | INFEASIBLE | UNKNOWN | UNK rate |
|---|---:|---:|---:|---:|
| Calibration, no window bounds, `[575, 1575)` | `1,000` | `799` | `201` | `20.10%` |
| Bounded, no window bounds, `[1575, 11575)` | `10,000` | `6,967` | `3,033` | `30.33%` |
| Bounded, with window bounds, `[1575, 11575)` | `10,000` | `9,835` | `165` | `1.65%` |
| Expansion, with window bounds, `[11575, 111575)` | `100,000` | `93,929` | `6,071` | `6.07%` |

The `20.10%` calibration rate was run *before* window-bounds were enabled
and is included for reference only; once window-cardinality pruning is on
(see §3.2), the residual sits in the `1`–`6%` band depending on the
chunk-ID range.

**Recursive refinement of `UNKNOWN` chunks.** Every chunk timing out at
the broad layer can be refined by extending the witness-pin prefix with the
next-degree split variables and re-solving the resulting subchunks. The number
of emitted rows is not a raw `2^d` fan-out: AP-prefix pruning eliminates many
descendants before a solver call is made. The retained refinement diagnostics
are shown below. The depth labels follow the L1/L2/L3/L4 refinement ladder of
§2.4.

| Stream | Source | Depth added | Rows emitted | INFEASIBLE | UNKNOWN |
|---|---|---:|---:|---:|---:|
| Sample-100 L1 | random sample of `100` broad UNKs | `+16` (to depth `40`) | `299,375` | `299,374` | `1` |
| Sample-100 tail | one Sample-100 residual | `+8` (to depth `48`) | `8` | `8` | `0` |
| Sample-500 L1 | stratified sample of `500` broad UNKs | `+16` (to depth `40`) | `2,076,105` | `2,076,095` | `10` |
| Sample-500 tail8 | `10` Sample-500 residuals | `+8` (to depth `48`) | `76` | `68` | `8` |
| Sample-500 level3 | `8` tail8 residuals | `+8` (to depth `56`) | `8` | `2` | `6` |
| Sample-500 level4 | `6` level3 residuals at `600`-s wall | `+8` (to depth `64`) | `6` | `6` | `0` |

The final Sample-500 level4 cleanup closed all `6` deep residuals within the
`600`-s cap, with a worst-case solver time of `599.74` s — within `0.26` s of
the cap, so this cleanup is at the practical limit of the refinement
strategy at its current parameter settings. Crucially, none of these
levels produced a `FEASIBLE` row.

The `6,071` `UNKNOWN` chunks of the expansion batch were *not* fully
refined by this campaign. Three subsets of them were sampled for
diagnostic experiments: a uniform random `100`-chunk recap study
(§3.2 and §4.2), a structural-mining analysis (§4.1), and the HiGHS
attack of §4.3.

\begin{figure}[t]
\centering
\resizebox{0.96\linewidth}{!}{%
\input{figures/t1_funnel.tex}
}
\caption{Funnel from the retained `100k` broad expansion batch to the final
two-chunk T1c residual. T1 is a `45`-chunk subset produced by recapping a
uniform random `100`-chunk sample of the `6,071` broad UNKNOWN chunks at
`300` seconds.}
\label{fig:t1-funnel}
\end{figure}

## 3.2 The window-cardinality A/B

The single most impactful intervention in the campaign was adding
window-cardinality inequalities derived from the OEIS A003002 b-file.
For every window `[a, a + L - 1] ⊆ [1, 212]` and every length `L` with
`r_3(L) < min(L, K)`, we add `sum_{i ∈ window} x_i ≤ r_3(L)`. For
`N = 212, K = 44` this generates `22,154` inequalities, on top of the
`11,130` 3-AP triple inequalities and the symmetry-breaking lex
constraint.

We measured the effect on three batches of varying size:

| Batch | Chunks | UNK without window-bounds | UNK with window-bounds | Reduction |
|---|---:|---:|---:|---:|
| `[575, 675)` | `100` | `27.00%` | `0.00%` | `−27.0 pp` |
| `[1575, 11575)` | `10,000` | `30.33%` | `1.65%` | `−28.7 pp` |
| `[11575, 111575)` | `100,000` | n/a | `6.07%` | — |

Both controlled A/Bs show a roughly `28`-percentage-point reduction in
`UNK` rate at the `60`-s broad wall cap. The window-bound family is
strictly stronger than the baseline 3-AP family at this problem size. In the
retained logs it also lowered total broad-pass solver time, because many
formerly hard chunks closed early under the extra bounds.

The `[575, 675)` A/B is a `100`-chunk subrange of the calibration range
reported in §3.1; the difference between its `27.00%` no-window `UNK` rate
and the calibration range's `20.10%` reflects the structural non-uniformity of
chunk-ID space rather than a change in model configuration.

However, the `UNK` rate is non-monotone in the chunk-ID range: the small
controlled A/B on `[575, 675)` closes to `0%`, the `10k` bounded batch
sits at `1.65%`, and the `100k` expansion batch sits at `6.07%`. This
indicates that the chunk-ID space is structurally non-uniform — later
chunk IDs (which encode different witness-pin assignments) are harder
in a way that window-bounds do not fully compensate for. The bucket
analysis in §4.1 quantifies this non-uniformity.

## 3.3 Solver configuration and engineering

All CP-SAT calls use the following configuration unless explicitly
overridden in an experiment:

- Model: decision-mode `sum_i x_i = 44`, `11,130` 3-AP linear
  inequalities, `22,154` window-cardinality inequalities, lex
  reflection symmetry break, endpoint forcing `x_1 = x_{212} = 1`.
- Branch strategy: variable selection by AP-incidence degree, value
  selection `min`, `fixed_search` to disable CP-SAT's portfolio.
- Solver: OR-Tools CP-SAT \cite{or-tools}, `8` workers per task, fixed solver seed
  and fixed search parameters, wall cap as noted (most commonly `60`-s
  for broad, `300`-s and `600`-s for recap experiments).

The SLURM emitter, shard collector, tail emitter, and proof-state manager
implement the workload pipeline. Output is
written as line-delimited JSON with one record per chunk; shards are
written to a temporary path and atomically renamed on completion so
that partial output from killed tasks cannot corrupt downstream
collection. The full campaign is reproducible end-to-end via the
`unity_handoff.sh` driver.

## 3.4 Zero FEASIBLE across the campaign

Aggregating across the broad pass, the refinement loop, the recap
studies, the lever experiments of §3.5, and the HiGHS attack of §4.3,
the campaign solved millions of `(N, K, fixed_in, fixed_out)` CP-SAT
subproblems, including prefix-closure work not tabulated above, `45`
HiGHS MIP subproblems, and the CDCL/SAT and proof-producing reruns reported
in §4.3. The number of
subproblems returning `FEASIBLE` is **zero**.

The `FEASIBLE` count is the only signal that would directly disprove
`r_3(212) ≤ 43`; its absence does not constitute a proof of the upper
bound, but it is strong empirical support, especially given that the
campaign forced the endpoints `1` and `212`, which any 44-set must contain by
the known value `r_3(211) = 43`, and then explored a depth-`24` prefix of the
verified 43-witness in the processed chunk ranges. Within the processed
expansion range, a 44-element 3-AP-free subset of `[1, 212]`, if one existed,
would have to lie in the `6,071` unresolved broad `UNKNOWN` chunks (or in
their deeper refinements). Globally, the much larger unprocessed remainder of
the full depth-`24` sweep remains open as well.

## 3.5 Search-tuning levers and their effect sizes

We tested five CP-SAT-side search-tuning levers. The
full lever inventory, including the HiGHS substitution and the
pair-AND Tseitin experiment, is consolidated in §4.4; here we report
only the three CP-SAT-side levers that operate at the broad layer.

| Lever | Mechanism | Bucket | Baseline UNK | Treatment UNK |
|---|---|---|---:|---:|
| Split-vars reorder | Permute the depth-`24` prefix so hot pins (values `{68, 75, 70, 76, 91}`) lead | `[61575, 66575)` | `13.60%` | `12.96%` |
| Wall-cap extension `60s → 300s` | Same model, same prefix, longer per-chunk budget | random `100` from expansion `UNK` | `100.00%` | `45.00%` |
| Recursive deepening | Refine `UNK` to depth `64` at `600`-s cap | `6` L3 residuals | `100.00%` | `0.00%` |

The reorder lever was tested for completeness but is expected to be a
null result on principle: the depth-`24` broad split iterates over the
`2^24` IN/OUT prefix assignments, and within-prefix variable ordering
does not change the set of surviving chunks under AP-prefix pruning
— only the order in which they are emitted to SLURM. The within-noise
result confirms this.

The wall-cap extension lever moves the residual substantially on the
first doubling but exhibits a saturating closure curve under further
extension. The `60s → 120s → 300s` series is analyzed in §4.2; in
brief, the marginal close-rate per additional second of wall drops
sharply past `300`-s, which is why the campaign did not pursue
`600`-s or `1200`-s broad-layer reruns on the full `6,071`-chunk
expansion residual.

The recursive-deepening lever, applied locally to small residual sets,
reliably closes individual deep `UNK` chunks (`6 / 6` at the L4 level
in §3.1). But the levers it implies — picking the next-degree split
variables and re-solving up to `2^8` descendant assignments at a longer wall —
do not
generalize cheaply to the full `6,071`-chunk expansion residual. A
naïve depth-`32` rerun on every expansion `UNK` would emit roughly
`1.5` million subproblems and require an order of magnitude more CPU
time than the original broad pass, with no guarantee of closing the
hard core analyzed in §4.

## 3.6 Compute budget

The retained logs provide measured solver wall time for the main diagnostics.
Since CP-SAT tasks used `8` workers, the worker-hour estimates below multiply
recorded solver-wall seconds by `8`; for HiGHS, the analogous estimate is
`8` threads per one-hour task. These are retained-log estimates, not exact
SLURM accounting totals.

| Layer | Worker-hours | Notes |
|---|---:|---|
| Retained broad logs | `~2,276` | includes the `10k` no-window run, the `10k` window run, the `100k` window run, and the `[575,675)` A/B |
| Sample-100 refinement | `~375` | depth-`40` plus one depth-`48` tail |
| Sample-500 refinement | `~1,978` | depth-`40`, depth-`48`, depth-`56`, and depth-`64` cleanup |
| Recap and worst-bucket A/Bs | `~598` | reorder, `300s` walltime, `120s` recap, `300s` recap |
| HiGHS attack on `45` survivors | `~360` | `1`-h wall, `8` threads per task |
| Full T1 HiGHS long-wall audit | `~2,002` | `45` T1 chunks, `8`-h cap, job `58782313`; estimated from retained `seconds` fields |
| T1b CDCL first run | `~19.8` | `20` single-core tasks, retained JSON row time `71,216.85` seconds |
| T1b proof-producing rerun + T1c diagnostic | `~120` | proof emission + 4-cell T1c grid |
| drat-trim verification | `~61` | jobs `58952708`, `59058393`, and `59383874`; all `18` CDCL-resolved `T1b ∖ T1c` chunks VERIFIED |
| Total retained logs | `~7,850` worker-hours | excludes interactive debugging and logs not retained locally |

The campaign fits comfortably within the `pi_ergezerm_wit_edu` SLURM
allocation on the `cpu` partition. The dominant retained costs are the
`100k` broad expansion, the sample-500 refinement, and the full-T1 long-wall
audit; the CDCL and certificate diagnostics are comparatively cheap. We note
for context that
a full depth-`24` sweep of the `12,582,912` AP-pruned chunks of the
witness-split lattice would require orders of magnitude more worker-hours
under the current architecture. More importantly, it is not justified by the
present evidence: the hard pocket of §4 is the binding obstacle, not simply
broad-layer throughput.
