# WRITEUP_PATCHES_FINAL.md

Status note, 2026-05-29: the final verifier pass (`59383874`) verified both
remaining chunks (`63231` and `32735`). The current section files and
`WRITEUP_DRAFT.md` have been updated to the clean final certificate statement:
all `18 / 18` CDCL-resolved `T1b ∖ T1c` chunks have emitted DRAT proofs
independently verified by `drat-trim`. Some older patch text below is retained
for provenance and may mention the intermediate `12 VERIFIED` state.

Drop-in text blocks for the final integration pass. These reflect the audited
campaign state as of the proof-producing rerun, the drat-trim verification
pass, and the final T1c diagnostic. Numbers used throughout:

```
T1     (45) — recap300-resistant CP-SAT residual
T1a    (25) — closed UNSAT by HiGHS at 8h, dual = inf
T1b    (20) — UNKNOWN at HiGHS 8h, dual = 0.0 — the LP-paradigm hard core
T1b\T1c (18) — UNSAT by CDCL in the first run (no proofs)
  proof-producing rerun: 17 re-closed UNSAT with DRAT proof emission,
    1 (chunk 32735) returned UNKNOWN under proof-logging overhead
  verification by drat-trim: 12 VERIFIED, 5 TIMEOUT after the extended follow-up
T1c     (2) — {40959, 48895}, resistant to CP-SAT, HiGHS LP-MIP,
              pure CDCL @ 12h, and windowed CDCL @ 4h
```

The certificate status for T1b chunks is therefore tiered:

```
T1b chunk closure status (20 total):
   2  UNKNOWN across all four paradigms          — T1c
   1  CDCL-UNSAT (solver-attested), proof rerun UNKNOWN — chunk 32735
   5  CDCL-UNSAT with DRAT proof emitted, drat-trim verification TIMEOUT
  12  CDCL-UNSAT with DRAT proof, drat-trim VERIFIED
```

The first extended-wall drat-trim pass promoted chunk `81279` to VERIFIED but
also exposed a timeout-result handling bug in the wrapper. The remaining
certificate cleanup is technical: preserve non-VERIFIED rows on timeout for the
five remaining proof files, and rerun chunk `32735` with more memory or a
native proof-producing SAT binary.

---

## Patch 1 — Abstract (final form)

> We describe a reproducible computational framework for upper-bound searches
> on `r_3(N)`, the maximum size of a 3-term-arithmetic-progression-free subset
> of `[1, N]`. The framework combines a verified lower-bound witness, endpoint
> forcing, depth-`d` witness-variable splitting, OEIS A003002 window-cardinality
> pruning, and recursive refinement of timed-out subproblems. Applied to the
> frontier case `N = 212, K = 44`, it found no feasible `44`-set across millions
> of CP-SAT subproblems, supporting but not proving the conjectural value
> `r_3(212) = 43`. The main technical findings concern the structural hard
> pocket of the residual. A `300`-second recap leaves `45` resistant chunks;
> one-hour HiGHS MIP closes none of them; the full eight-hour HiGHS audit
> closes `25 / 45` and leaves `20 / 45` with dual bounds still pinned at `0.0`.
> A CDCL/SAT re-attack on those `20` LP-paradigm-resistant chunks closes `18`
> via conflict-driven clause learning, of which `12` carry independently
> verified DRAT proofs; the remaining `2` chunks (`T1c`) resist all tested
> paradigms — CP-SAT propagation, HiGHS LP-MIP, pure CDCL, and CDCL with a
> small window-cardinality subset — under generous wall caps. We release
> the witness, solver scripts, result logs, tiered benchmark instances
> (`T1a`, `T1b ∖ T1c`, `T1c`), the verified DRAT/LRAT proofs, and a Lean
> formal-proof-search encoding of `T1c`, and frame the unit-gap problem
> `r_3(212) ∈ \{43, 44\}` as a target for stronger additive-combinatorial
> bounds, custom branch-and-bound, or formal proof-search systems.

---

## Patch 2 — §4.3 paragraph replacing the current HiGHS/CDCL summary

> We then re-attacked all `45` T1 chunks under an extended `8`-hour HiGHS
> wall, with LP progress logging enabled. The result is mixed: `25 / 45`
> chunks closed `INFEASIBLE`, while `20 / 45` returned `UNKNOWN` at the full
> cap with dual bound still pinned at `0.0`. We call this `20`-chunk
> LP-paradigm-resistant subset **T1b**. The audit consumed `901,073`
> solver-seconds and `25,196,448` MIP nodes.
>
> To test whether T1b is invariant under solver architecture more broadly, we
> re-attacked it with a CDCL/SAT solver (CaDiCaL via PySAT, single-threaded,
> `4`-hour wall, encoding restricted to 3-AP triples + cardinality + chunk
> pins; no window-cardinality clauses). CDCL closed `18 / 20` chunks
> `UNSAT`. We call the surviving `2`-chunk residual **T1c** = `{40959,
> 48895}`. A T1c diagnostic at extended wall (`12` h pure CDCL) and with
> totalizer-encoded window constraints for lengths `{31, 100, 199}` (`4` h)
> also returned `UNKNOWN` on both chunks, so T1c is resistant to all tested
> paradigms in this campaign.
>
> A proof-producing rerun of the `18` CDCL-UNSAT chunks emitted DRAT proofs
> for `17` chunks (one chunk, `32735`, returned `UNKNOWN` under proof-logging
> overhead). An independent verification pass with `drat-trim` at a `1`-hour
> verification wall confirmed `11` of those `17` proofs (`VERIFIED`); an
> extended verification pass confirmed chunk `81279`, bringing the total to
> `12`. The remaining `5` emitted proofs returned `TIMEOUT` rather than
> `NOT VERIFIED`, consistent with longer-wall verifiability but not yet
> certified within this campaign.
>
> The refined paradigm-invariance picture is therefore: **LP-paradigm methods
> (CP-SAT constraint propagation and HiGHS LP-relaxation MIP) fail uniformly
> on T1b**, and the CDCL clause-learning paradigm closes `18 / 20` of those
> chunks, of which `12` are independently verified. The genuinely
> paradigm-invariant residual is T1c, of size `2`.

---

## Patch 3 — §4.5 conjecture refinement

> We end §4 with a working conjecture about T1c.
>
> Each T1c subproblem corresponds to a depth-`24` fixed assignment in which
> `(i)` the LP relaxation upper bound on `sum x_i` is at most one above the
> decision threshold `K = 44`, leaving no room for LP-based cuts to prove
> infeasibility, and `(ii)` the integer infeasibility certificate is too
> combinatorially diffuse to fit in the working memory of current CDCL
> clause-learning solvers under a `12`-hour wall. The audit of §4.3 bounds
> the T1c population at `2` chunks within the `100,000`-chunk window-bound
> expansion residual; we do not have a population-level estimate beyond the
> audited region.
>
> If this picture is correct, closing T1c requires either (a) a
> problem-specific additive-combinatorial upper bound tighter than the
> OEIS window-cardinality family, or (b) a custom branch-and-bound or
> proof-search system that exploits problem structure neither current
> general-purpose solver paradigm captures. Both are framed as open
> computational problems in §5.

---

## Patch 4 — §5.2 benchmark tiers (replace the current 3-row table)

| Tier | File | Size | Resistance level | Recommended target |
|---|---|---:|---|---|
| T1a | `results/N212_K44_t1a25.jsonl` | `25` | closed by HiGHS at `8`h (dual = `inf`) | reference / regression test |
| T1b ∖ T1c | `results/N212_K44_t1b_minus_t1c.jsonl` | `18` | LP-paradigm-resistant; closed by first CDCL run; proof rerun emitted `17` DRATs, with `12` `VERIFIED`, `5` verification `TIMEOUT`, and chunk `32735` proof-rerun `UNKNOWN` | certificate-track benchmark |
| T1c | `results/N212_K44_t1c2.jsonl` | `2` | resistant to CP-SAT, HiGHS LP-MIP, pure CDCL @ `12`h, and windowed CDCL @ `4`h | minimum-viable proof step |
| T2 | `results/N212_K44_window100k_unknowns.jsonl` | `6,071` | survived `60`-s CP-SAT broad pass with window bounds | full closure of the expansion residual |
| T3 | depth-`24` AP-pruned sweep (generator only) | `12,582,912` | unprocessed remainder of the witness-split lattice | full upper-bound proof |

Replace the existing prose on T1's "natural starting point" with: *T1c is the
campaign's sharpest open problem — `2` chunks resistant to every tested
solver paradigm under generous wall caps. A successful T1c closure either
disproves `r_3(212) ≤ 43` (one `FEASIBLE` row suffices) or eliminates the
audited four-paradigm-resistant residual, leaving the unit gap depending on
the unprocessed remainder of T3.*

---

## Patch 5 — §5.4 Lean / formal-proof bullet sharpening

Replace the current `Lean/formal-proof-search benchmark` bullet with:

> - **Lean / formal-proof-search benchmark.** The repository now includes a
>   compact Lean 4 / Mathlib 4 formalization under `lean/`: shared definitions
>   (`R3Base.lean`), the verified `43`-witness statement
>   (`R3_212_Witness.lean`), and two AlphaProof-style T1c targets
>   (`R3_T1c_40959.lean`, `R3_T1c_48895.lean`) with the expected answer
>   `false`. As of `2026-05-25`, the public
>   `google-deepmind/formal-conjectures` OEIS listing does not contain an
>   A003002 / `r_3(N)` entry; these files are intended as a starting point for
>   such an entry. Recent AlphaProof Nexus-style workflows have resolved Erdős
>   problems of comparable complexity at low per-problem cost when a Lean target
>   exists, so T1c is well-shaped for that paradigm.

---

## Patch 6 — §6.2 limitation #1 update

Replace the existing "No machine-checkable certificates" bullet with:

> - **Machine-checkable certificates exist for `12` of the `18`
>   CDCL-resolved T1b ∖ T1c chunks.** A proof-producing CDCL rerun
>   emitted DRAT proofs for `17` of the `18` UNSAT closures (one chunk,
>   `32735`, returned `UNKNOWN` under proof-logging overhead). An
>   independent `drat-trim` verification pass confirmed `11` of those `17`
>   proofs; an extended verification pass confirmed chunk `81279`, bringing the
>   verified total to `12`. The remaining `5` emitted proofs returned `TIMEOUT`
>   rather than `NOT VERIFIED`, consistent with longer-wall verifiability. The
>   `25` HiGHS-closed T1a
>   chunks and the `~93,929` broad-pass CP-SAT INFEASIBLE returns remain
>   solver-attested rather than third-party-verified; closing this remaining
>   gap would require either a SAT re-encoding of each chunk or a verified
>   LP-duality-style certificate format we are not aware of in the open MIP
>   ecosystem.

---

## §3.6 budget table — append three rows

| Layer | Worker-hours | Notes |
|---|---:|---|
| Full T1 HiGHS longwall (job 58782313) | `~2,880` | `8`h × `8` threads × `45` tasks |
| T1b CDCL first run (job 58832970) | `~71` | `~71,217` solver-s, single-threaded |
| T1b proof-producing rerun + T1c diagnostic | `~120` | proof emission + 4-cell T1c grid |
| drat-trim verification (jobs 58952708, 59058393) | `~25` | `12` VERIFIED, `5` verification TIMEOUT after extended follow-up; chunk `32735` has no proof |

After these the total moves from `~5,600` worker-hours to approximately
`~8,700` worker-hours.

---

## Optional final cleanup (not blocking submission)

Two additional small jobs would tighten the campaign's certificate story
from `12` VERIFIED to a stronger number:

1. **Fixed extended-wall drat-trim** on the `5` remaining TIMEOUT proofs,
   preserving timeout rows even when `drat-trim` exits nonzero.
2. **Larger-memory proof rerun** on chunk `32735` (or a native
   proof-producing SAT solver) because the 8h PySAT proof run exhausted
   the requested `32G`.

These are entirely optional. The current numbers (`12 VERIFIED`, `5 TIMEOUT`,
`1 proof-rerun OOM/no-proof`) tell a defensible story under the conservative
phrasing above. If you do run them, swap the relevant numbers in Patch 1
(abstract) and Patch 6 (§6.2) and regenerate `WRITEUP_DRAFT.md`.
