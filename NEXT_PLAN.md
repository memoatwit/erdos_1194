# NEXT_PLAN.md — forward-looking research plan

`PLAN.md` is the historical record of phases already executed.
This file is the forward-looking plan: what to ship next.

## Current state (as of session 7, 2026-05-11)

Proven (`proofs/lower_bound_io.tex`, 6 pp):
- $a_n \gg n \log n$ i.o. (Theorem 1, classical).
- $a_n \gg n^{2-o(1)}$ i.o. (Theorem 4, partition identity).
- $a_n \gg n^2/f(n)$ i.o. for slowly varying $f$ with
  $\sum 1/(nf(n)) < \infty$ (Theorem 5).

Strong empirical:
- Finite PDS optimum $M^*(N) \approx 2N$ for $N \in [20, 45]$ (Phase 4).
- Forced extension from any seed grows like $N^{4+}$ (Phase 4').
- Mian–Chowla-seeded greedy reduces upper bound constant 11× (Phase 3').

Open:
- $a_n \gg n^c$ i.o. with $c > 2$.
- $a_n = o(n^3)$ — CiNa08 Problem 1.
- $a_n \gg n^c$ for all large $n$ — Phase 4' conjecture.

## Candidate next phases (in order of ship-ability)

### Phase 5 — Research note (recommended first)

Consolidate everything into a self-contained 10–15 page note suitable
for `erdosproblems.com/1194` as a forum comment or for arXiv preprint.

**Outline:**
1. Setup and known bounds.
2. Lower bound (i.o.): Theorems 1, 4, 5.
3. Finite optima (Phase 4): $M^*(N) \approx 2N$ exact values.
4. Extension obstruction (Phase 4'): $N^4$ forced blow-up.
5. Constructive upper bound (Phase 3'): seeded greedy.
6. Open problems: $c = 2$ barrier, CiNa08 Problem 1, Phase 4' conjecture.
7. Code / data appendix.

**Effort:** 1–2 sessions.
**Risk:** none.
**Outcome:** shippable artifact.

### Phase 6 — Block-structured construction

**STATUS: Done (session 9, 2026-05-11). Result: no-go.** Built and tested
`split_MC` (disjoint MC chunks) and `AP_MC` (arithmetic progression of
chunks). Best variant gives ratio 0.00224 at $N=500$ — only marginally
below MC(60)'s 0.00229. **The $\Theta(N^3)$ ceiling holds across all
block-structured seeds.** Constant settles near $\approx 0.002 N^3$.

**Reason** (now empirically established): once the seed is fixed, the
greedy *continuation* has per-call cost $\Theta(N^2)$ regardless of seed
structure. This drives the cubic. **Beating $o(n^3)$ requires
non-greedy continuation, not better seeds.** See
`results/phase6_summary.md`.

CiNa08 Problem 1 remains open.

### Phase 2A — Sharper Sidon density for PDS

**STATUS: Attempted, no theorem (session 10, 2026-05-13).** Three
structural attempts documented in `proofs/phase2a_density.tex` (5pp):

1. Cauchy–Schwarz via partition identity → fails because $a_n$ is
   non-monotone, so the "covered prefix" $T_M$ can be much less than
   $\binom{k(M)}{2}$.
2. Fejér-weighted Plancherel → only useful upper bound is $|\widehat 1|^2
   \leq k^2$, trivialising to Sidon.
3. Higher $L^p$ moments → determined by Sidon alone, no PDS info.

**Structural reason:** PDS vs Sidon shows up in *which* small
differences appear, not in aggregate counting. The Phase 2C partition
argument is the unique elementary tool and caps at $c = 2$.

**Three sub-targets remain open:**
- Density-zero exceptional set: $\{x : k(x) > (1-\delta)\sqrt x\}$ has
  density 0 in $\mathbb{N}$.
- Close the 0.293 gap between CiNa08 ($1/\sqrt 2$) and Lindström ($1$).
- Positive-density Phase 2C: strengthen i.o.\ form of $a_n \gg n^{2-o(1)}$
  to "$a_n \gg n^c$ at positive density of $n$".

See `results/phase2a_summary.md` for the honest write-up.

### Phase 7 — Lean formalization

**STATUS: Done (session 11, 2026-05-13).** Wrote `formal/1194.lean`,
a Lean 4 / Mathlib file matching the
[`google-deepmind/formal-conjectures`](https://github.com/google-deepmind/formal-conjectures)
format. The file declares:

- `IsPDS` (definition), plus `aFun`, `bFun`, `kFun`.
- Supporting lemmas: `isPDS_imp_sidon`, `pds_counting`,
  `pds_partition_consequence`, `gap_bound`.
- Solved theorems: `lev_upper_bound` ($a_n \ll n^3$),
  `thm1_n_log_n_io`, `thm4_n_two_minus_o_one_io`,
  `thm5_n_squared_over_f_io`, plus the corollary
  `thm5_corollary_n_over_log_squared`.
- Open conjectures: `cina08_problem1` ($a_n = o(n^3)$?) and
  `extension_lower_bound_conjecture` (Phase 4' for-all-$n$ form).

All proofs are `sorry` for now — the artifact value is the formal
statement, as is conventional in `formal-conjectures`. Doc-comments
on each theorem give a proof sketch and a pointer back to the prose
proof in `proofs/erdos_1194_note.tex`.

Submission path: fork the repo, drop the file at
`FormalConjectures/ErdosProblems/1194.lean`, verify `lake build`,
open a PR. See `formal/README.md` for the full submission notes.

## Recommended ordering

1. ~~**Phase 5** (writeup).~~ **DONE — session 8.** 8-page note.
2. ~~**Phase 6** (block construction).~~ **DONE — session 9. No-go.**
3. ~~**Phase 2A** (density theorem hunt).~~ **DONE — session 10. No theorem.**
   Documented as a deliberate no-go with three failed attempts + three
   sub-targets for future work.
4. ~~**Phase 7** (Lean formalization).~~ **DONE — session 11.**
   `formal/1194.lean` ready for submission to
   `google-deepmind/formal-conjectures`.
5. ~~**Phase 8** (#42/#43 Sidon disjoint-difference pivot).~~ **CLOSED.**
   The local `erdos_42/` work attacked the #43 binomial-gap problem, but
   the public pages have moved: #42 is marked solved and #43 is marked
   disproved as of 2026-05-14. Keep the CP-SAT code as a verification
   harness, but do not continue this as the main solve path.
6. **Phase 9 — Erdős #156 maximal Sidon sets.** **ACTIVE NEXT.**
   Goal: compute exact small values of the minimum size of an inclusion-
   maximal Sidon set in `[1,N]`, search for structure, and look for a
   route from Ruzsa's $\ll (N\log N)^{1/3}$ construction to the desired
   $O(N^{1/3})$. Handoff: `erdos_156/phase9_plan.md`.

## Why this order

- Phase 5 turns a fragmented body of work (proofs/, results/, README
  sections) into a single citeable artifact. No risk; clear value.
- Phase 6 is the most concrete way to address CiNa08 Problem 1 with
  the existing seeded-greedy infrastructure.
- Phase 2A and Phase 7 are alternatives at the end: 2A is high-risk
  theorem hunt, 7 is a low-risk artifact play.

## Stop conditions

- After Phase 5: if the note compiles to PDF and is clean, that's a
  shippable session.
- After Phase 6: if no construction beats $\Theta(N^3)$, write that
  up as a no-go theorem and stop.
- Phase 2A: if no clear lemma path emerges within a session, pivot
  back to writeup additions.
