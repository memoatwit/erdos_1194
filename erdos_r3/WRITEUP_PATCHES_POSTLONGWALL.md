# Post-longwall writeup patch kit

This file is a morning-after patch guide for Unity job `58782313`, the full
T1 HiGHS 8-hour long-wall audit over all `45` recap300 survivors.

After the job completes:

1. Aggregate `results/highs_t1_longwall45/*.jsonl`.
2. Verify `FEASIBLE = 0` before doing any prose updates.
3. Fill in the placeholders below:
   - `CLOSED = count(INFEASIBLE)`
   - `UNKNOWN = count(UNKNOWN)`
   - `TOTAL_SECONDS = sum(seconds)`
   - `TOTAL_NODES = sum(mip_nodes)`
   - `DUAL_UNKNOWN_SUMMARY = e.g. "all UNKNOWN rows retained dual bound 0.0"`

## §4.3 Replacement Paragraphs

Replace the current five-chunk pilot paragraph in §4.3 with one of the following
blocks.

### Scenario A: pilot rate roughly holds

Use this if `CLOSED` is in the broad range `20..35`.

```text
We then re-attacked all `45` T1 chunks under an extended `8`-hour wall, with
HiGHS progress logging enabled. The result was mixed: `CLOSED / 45` chunks
closed `INFEASIBLE`, while `UNKNOWN / 45` returned `UNKNOWN` at the full cap.
The run consumed `TOTAL_SECONDS` solver-seconds and `TOTAL_NODES` MIP nodes.
Among the unresolved rows, `DUAL_UNKNOWN_SUMMARY`. Thus the one-hour HiGHS pass
was too pessimistic — a substantial intermediate class is long-wall closable —
but the full audit leaves a smaller hard core with the same flat-dual signature
seen in the five-chunk pilot.
```

Then replace the current following interpretation paragraph with:

```text
This is the strongest empirical finding of the campaign, but its precise
meaning is narrower than the one-hour result alone suggested. T1 separates into
an intermediate class, resolvable by multi-hour MIP search, and a smaller hard
core that retains the signature predicted by §4.5: uninformative dual bounds
despite large branch-and-bound trees. The solver-paradigm invariance claim
therefore applies to this audited hard core, not uniformly to all `45` original
T1 survivors.
```

### Scenario B: almost everything closes

Use this if `CLOSED >= 40`.

```text
We then re-attacked all `45` T1 chunks under an extended `8`-hour wall, with
HiGHS progress logging enabled. This changed the interpretation materially:
`CLOSED / 45` chunks closed `INFEASIBLE`, leaving only `UNKNOWN / 45` unresolved
after `TOTAL_SECONDS` solver-seconds and `TOTAL_NODES` MIP nodes. Among the
unresolved rows, `DUAL_UNKNOWN_SUMMARY`. The hard pocket is therefore much
smaller than the 300-second CP-SAT and one-hour HiGHS runs suggested; for most
T1 instances, the obstacle is wall time rather than a fundamentally flat MIP
relaxation.
```

Then replace the current following interpretation paragraph with:

```text
The solver-paradigm invariance claim should therefore be restricted sharply. A
small long-wall-resistant core remains, but most of T1 is not intrinsically
solver-invariant; it is expensive. The remaining benchmark target is the
unresolved subset, not the full original `45`-chunk T1 population.
```

### Scenario C: very little closes

Use this if `CLOSED <= 10`.

```text
We then re-attacked all `45` T1 chunks under an extended `8`-hour wall, with
HiGHS progress logging enabled. The result strengthened the hard-pocket
interpretation: only `CLOSED / 45` chunks closed `INFEASIBLE`, while
`UNKNOWN / 45` returned `UNKNOWN` at the full cap. The run consumed
`TOTAL_SECONDS` solver-seconds and `TOTAL_NODES` MIP nodes. Among the unresolved
rows, `DUAL_UNKNOWN_SUMMARY`. Thus even an eight-fold wall increase over the
one-hour MIP pass leaves most of T1 untouched.
```

Then replace the current following interpretation paragraph with:

```text
This is the strongest empirical finding of the campaign. The hard pocket is not
a constraint-propagation artifact; most of it survives substitution of the
solver's core inference engine even under multi-hour MIP caps. Both major
paradigms applicable at this problem size — CP-SAT-style constraint propagation
and LP-relaxation-based branch-and-cut — fail in essentially the same way on the
audited T1 population.
```

## §5.2 Table and Paragraph Patch

Update the T1 row to:

```text
| T1 | `results/N212_K44_broad24_recap300_residual45.jsonl` | `45` chunks | survived `300`-s CP-SAT recap and `3600`-s HiGHS MIP; full `8`-hour HiGHS audit closed `CLOSED / 45`, leaving `UNKNOWN / 45` | minimum-viable proof step |
```

Replace:

```text
We have not yet audited this split across all `45` chunks.
```

with:

```text
The full-T1 long-wall audit closes `CLOSED / 45` chunks and leaves
`UNKNOWN / 45`; these unresolved rows are the current T1b hard core.
```

## §3.6 Compute Budget Patch

Add a row to the retained-log worker-hour table:

```text
| Full T1 HiGHS long-wall audit | `45` T1 chunks, `8`-hour cap, job `58782313` | `~2,880` |
```

Then update the text total:

```text
The retained-log compute budget is therefore about `~8,500` worker-hours after
including the full-T1 long-wall audit.
```

If many rows closed much earlier than `8` hours, optionally replace `~2,880`
with an audited sum from the `seconds` field:

```text
worker_hours = sum(seconds) * 8 / 3600
```
