# 2. Architecture

The campaign rests on five components: a decision-form CP-SAT model
of the 3-AP-free subset problem (§2.1), a witness-variable splitting
scheme that produces tractable subproblems (§2.2), a window-cardinality
pruning family derived from OEIS A003002 (§2.3), a recursive refinement
loop for residual `UNKNOWN` chunks (§2.4), and the SLURM-side
engineering that makes the workload reproducible (§2.5). Each
component is independent of the others — any could be replaced by a
stronger variant without disturbing the rest — and together they
define the proof attempt on `r_3(212) ≤ 43`.

## 2.1 Decision-form CP-SAT model

Fix `N ≥ 3` and `K ≥ 3`. The standard CP-SAT encoding of "does there
exist a 3-AP-free subset `A ⊆ [1, N]` with `|A| ≥ K`?" introduces
Boolean variables `x_i ∈ \{0, 1\}` for `i ∈ [1, N]` with `x_i = 1`
iff `i ∈ A`, and adds the constraints

```
  x_a + x_b + x_c ≤ 2     for every 3-AP triple (a, b, c),
  sum_i x_i ≥ K.
```

We adopt the **decision-form** variant in which the second inequality
is replaced by the equality

```
  sum_i x_i = K.
```

The decision-form encoding is tighter for propagation, not for logical
interpretation of `UNKNOWN`: an `UNKNOWN` return on either encoding is still
consistent with both feasibility and infeasibility. The practical advantage of
`sum_i x_i = K` is that CP-SAT and pseudo-Boolean propagators see both the
lower and upper cardinality directions. Branches that would require more than
`K` selected values, or too few remaining unfixed values to reach `K`, can be
cut earlier than in the inequality form. For our purposes (proving the upper
bound `r_3(N) ≤ K - 1`), the equality form is therefore the right primitive.

For `N = 212, K = 44`, the model has `212` Boolean variables and
`11,130` 3-AP triple inequalities. We add the lex symmetry-breaking
constraint

```
  (x_1, x_2, ..., x_N)  ≥_lex  (x_N, x_{N-1}, ..., x_1)
```

to factor out the reflection `i ↦ N + 1 - i`. The opposite orientation would
be equivalent; the implementation uses `≥_lex`. We do not add other
symmetries. After endpoint forcing, reflection is the only order-preserving
symmetry we exploit.

We also apply **endpoint forcing** specific to the `r_3(212)` case.
Since OEIS A003002 records `r_3(211) = 43`, any `44`-element
3-AP-free subset of `[1, 212]` must contain both endpoints `1`
and `212`: if `1` were absent, the set would be a `44`-element
3-AP-free subset of `[2, 212]`, which shifts to `[1, 211]`; if `212`
were absent, it would already lie in `[1, 211]`. Either case contradicts
`r_3(211) = 43`. We add `x_1 = x_{212} = 1` as ground assumptions in
every chunk.

Branching: variable selection by AP-incidence degree (the number of
3-AP triples a variable appears in), value selection `min`, and
`fixed_search` to disable CP-SAT's portfolio search. The first two
target the most-constrained variables first; the third reduces solver-policy
variation across runs, which is necessary for the A/B experiments of §3.2
and §3.5.

## 2.2 Witness-variable splitting

The decision-form model on the full range `[1, 212]` is already at
the limit of single-call CP-SAT solving in reasonable wall time. To
break it into tractable subproblems we use the verified `43`-element
lower-bound witness `A_43 ⊂ [1, 212]` (§2.1, §3.1) as a guide. The
splitting proceeds in three steps.

**Degree ranking.** For each `v ∈ A_43`, compute the AP-incidence
degree `deg(v) = |\{(a, b, c) : v \in \{a, b, c\}, b - a = c - b\}|`.
Sort `A_43` by `deg(v)` in decreasing order. Pick the top
`d = 24` witness values; we refer to this prefix as the **broad split
prefix**.

**Combinatorial enumeration.** For each of the `2^24 = 16,777,216`
IN/OUT assignments of the broad split prefix, instantiate a
**chunk**: the decision-form model with `x_v` fixed to the chosen
value for every `v` in the prefix. A chunk is identified by its
`24`-bit chunk ID.

**AP-prefix pruning.** Many chunks are immediately infeasible at the
3-AP level alone: if the broad split prefix forces three pinned-IN
values that form a 3-AP, the chunk has no feasible completion and
need not be sent to CP-SAT. We perform this check during chunk
emission and skip such chunks. The surviving chunk count for
`N = 212, K = 44` at depth `24` is `12,582,912`, roughly `75%` of
the raw `2^24` count.

The choice `d = 24` is empirical: larger `d` produces more chunks but
each is easier; smaller `d` produces fewer chunks but each is harder.
At `d = 24` the per-chunk solver time at the `60`-s wall cap has a
heavy tail but a tractable median (the broad pass closes `~94%` of
expansion chunks within `60` s — see §3.1), which makes the depth
`24` choice a workable broad layer.

## 2.3 Window-cardinality pruning from OEIS A003002

The 3-AP-free subset problem admits a family of valid inequalities
that are not implied by the 3-AP triple inequalities alone. For
any window `[a, a + L - 1] ⊆ [1, N]` and any length `L` with
`r_3(L) < L`,

```
  sum_{i ∈ [a, a+L-1]}  x_i  ≤  r_3(L).
```

This is valid because `\{i ∈ A : i ∈ [a, a + L - 1]\}` is itself a
3-AP-free subset of an `L`-element interval, hence of size at most
`r_3(L)`. Crucially, the right-hand side `r_3(L)` is *constant* with
respect to `a`, so the family is a single constant per window length,
not a learned bound.

We populate the right-hand sides from the OEIS A003002 b-file
(Cariboni's tabulation, valid for `L ≤ 211`). For `N = 212, K = 44`
we generate window constraints for every available length `L` with
`r_3(L) < min(L, K)` and every `a ∈ \{1, 2, …, 212 - L + 1\}`. The
resulting model contains `22,154` window inequalities.

Empirically the window family is the single most impactful CP-SAT
intervention in the campaign: the controlled A/Bs of §3.2 show a
`~28`-percentage-point reduction in `UNK` rate at the `60`-s wall
cap when window-bounds are enabled. We use it as the default
configuration for every solver call beyond the calibration batch.

## 2.4 Recursive refinement

A chunk that returns `UNKNOWN` at the broad layer is refined by
extending the broad split prefix with the next `m` witness values
(by AP-incidence degree) and re-emitting the resulting `2^m`
subchunks (less AP-prefix pruning) to the solver under a longer
wall cap. The depths and per-step parameters used in the campaign
are:

| Level | Depth | Step size `m` | Per-chunk wall cap |
|---|---:|---:|---:|
| Broad | `24` | — | `60` s |
| L1 | `40` | `+16` | `60` s |
| L2 (tail) | `48` | `+8` | `60` s |
| L3 (level3) | `56` | `+8` | `60` s |
| L4 (level4) | `64` | `+8` | `600` s |

Each level is fed only the `UNKNOWN` residuals of the prior level,
so the work at deeper levels is concentrated on the hard tail. The
expected per-level fan-out `2^m` is mitigated by AP-prefix pruning,
which becomes more aggressive at deeper levels (more pinned-IN
values, more chances for a 3-AP among them). For example, the
Sample-500 L1 stream emits `2,076,105` rows from `500 × 2^16`
nominal descendants, a `~6%` survival rate after pruning.

Refinement is the campaign's primary tool for closing residual
`UNKNOWN` chunks. It reliably closes individual deep chunks
(§3.1 reports `6 / 6` closure at L4). It does not generalize
cheaply to the full `6,071`-chunk expansion residual because the
per-chunk cost grows roughly geometrically with depth.

## 2.5 SLURM engineering

The campaign runs on the UMass Unity SLURM cluster. The workload
pipeline is implemented as a small collection of Python scripts,
each with a single responsibility:

- **`r3_slurm_emit.py`** — generates the chunk-ID list for a given
  `(N, K, split-vars, depth, range)` and emits a SLURM array
  `sbatch` script that fans out the chunks across array tasks. The
  `--chunks-per-task` flag controls the granularity of fan-out.
- **`r3_split_cpsat.py`** — the per-task driver. Reads its slice of
  chunk IDs, instantiates the CP-SAT model for each, runs the solver
  under the per-chunk wall cap, and appends one JSONL row per chunk
  to a shard file.
- **`r3_collect.py`** — merges shard files into the canonical batch
  output. Handles deduplication if a chunk was solved more than
  once (e.g., during retries).
- **`r3_tail_emit.py`** — emits the next-level refinement workload
  from the `UNKNOWN` rows of a parent batch. Supports multi-parent
  inputs (each input JSONL contributing its own parent prefix) and
  templated output naming via a parent-tag regex.
- **`r3_proof_manager.py`** — tracks the proof-state graph across
  levels, identifying which chunks have been closed at which depth
  and which remain open.
- **`r3_verify.py`** — independent triple-enumeration verifier for
  any candidate `K`-element witness.

Two engineering decisions are worth highlighting because they affect
reproducibility:

**Atomic shard renames.** Each per-task driver writes its shard to
a temporary `.tmp` path keyed by the SLURM job and array IDs, and renames it
to `shard.jsonl` on successful completion. A killed or pre-empted
task leaves only the temporary file, which is ignored by the
collector. This pattern prevents partial output from corrupting
downstream collection without requiring any locking.

**Deterministic inputs.** Every chunk ID maps to a fixed prefix assignment,
and every CP-SAT call uses the same solver seed and fixed-search branching.
This is necessary for the lever A/B experiments of §3.5: a "no measurable
effect" claim is only defensible if the baseline arm is reproducible under
the same software stack.

The end-to-end pipeline is driven by `unity_handoff.sh`, which
runs the broad pass, the recap studies, the refinement levels, and
the HiGHS attack as separately resumable phases. A complete
campaign reproduction on a fresh allocation requires the OEIS
b-file, the verified `43`-witness, the Python environment
(OR-Tools, `highspy`, PySAT/CaDiCaL, and `drat-trim`), and a SLURM allocation;
everything else is
generated by the scripts.
