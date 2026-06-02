# Lean formalization — Erdős Problem #1194

This directory contains a Lean 4 (Mathlib) formalization of the
statements proved (and conjectured) in the companion research note
`proofs/erdos_1194_note.tex`.

## Contents

- `1194.lean` — Lean file in the format of
  [`google-deepmind/formal-conjectures`](https://github.com/google-deepmind/formal-conjectures).
  Path inside that repo: `FormalConjectures/ErdosProblems/1194.lean`.

## What is formalised

The file declares:

| Definition / Theorem | Description | Status |
|---|---|---|
| `IsPDS A` | A perfect difference set | def |
| `aFun`, `bFun`, `kFun` | The functions $a_n, b_n, k(x)$ from the note | def (noncomputable) |
| `isPDS_imp_sidon` | PDS implies Sidon | `sorry` |
| `pds_counting` | Lemma 1: $N(x) = \binom{k(x)}{2}$ | `sorry` |
| `pds_partition_consequence` | Lemma 2: $X = \sum_{k} |D_k \cap [1, X]|$ | `sorry` |
| `gap_bound` | Lemma 3: $a_n \leq Cn^c$ ⇒ $x_k \gg k^{c/(c-1)}$ | `sorry` |
| `lev_upper_bound` | $\exists$ PDS with $a_n \ll n^3$ | proven by Lev; `sorry` here |
| `thm1_n_log_n_io` | Theorem 1: $a_n \gg n \log n$ i.o. | proven; `sorry` here |
| `thm4_n_two_minus_o_one_io` | Theorem 4: $a_n \gg n^{2-o(1)}$ i.o. | proven; `sorry` here |
| `thm5_n_squared_over_f_io` | Theorem 5: $a_n \gg n^2/f(n)$ i.o. for slow-varying $f$ | proven; `sorry` here |
| `thm5_corollary_n_over_log_squared` | $a_n \gg (n/\log n)^2$ i.o. | corollary; `sorry` here |
| `cina08_problem1` | Open: does $\exists$ PDS with $a_n = o(n^3)$? | open since 2008 |
| `extension_lower_bound_conjecture` | Phase 4' conjecture: $a_n \gg n^c$ for all $n$ | open |

All theorems include doc-comments pointing at the relevant section
of `proofs/erdos_1194_note.tex` for the prose proof.

The `sorry`s mark places where the Lean proof would need to be
elaborated. The artifact's value is the formal STATEMENT, not the
proof. Following the
[formal-conjectures README](https://github.com/google-deepmind/formal-conjectures):

> While there is a growing corpus of formalised theorems including
> proofs, there is a lack of open conjectures where only the statement
> has been formalised.

## Submission path

To upstream this file:

1. Fork [`google-deepmind/formal-conjectures`](https://github.com/google-deepmind/formal-conjectures).
2. Copy `1194.lean` into `FormalConjectures/ErdosProblems/1194.lean`.
3. Verify it compiles via `lake build` against the repo's pinned Mathlib.
4. Open a PR with a link to:
   - `erdos_1194/proofs/erdos_1194_note.pdf` for full prose proofs;
   - `erdosproblems.com/forum/thread/1194` post 5745 for the original
     GPT-5.4 Pro / Bloom argument (Theorem 4);
   - this directory for accompanying empirical evidence.

The PR description should note that the file currently uses `sorry`
for all proofs; full Lean proofs of Theorems 1, 4, 5 are a natural
follow-on once the supporting lemmas (PDS counting, partition, gap
bound, plus the Halberstam–Roth i.o. Sidon density) are formalised
or located in mathlib.

## Notes for the Lean proof

The companion note `proofs/erdos_1194_note.tex` and
`proofs/lower_bound_io.tex` give fully rigorous prose proofs of
Theorems 1, 4, 5. Translating to Lean requires:

- **Sidon density i.o.** $|B \cap [1, x]| \ll \sqrt{x/\log x}$ for
  infinite Sidon `B`. This is the only nontrivial analytic ingredient
  in Theorem 1. It is *not* (as of this writing) in mathlib; a
  prerequisite formalisation may be needed.

- **The partition identity (Lemma 2).** Combinatorial; the proof is
  unique-representation chasing over the increasing enumeration of `A`.

- **The gap bound (Lemma 3).** A telescoping argument plus an ODE
  comparison ($dy/dk \asymp y^{1/c}$) — should not need anything
  beyond elementary calculus / `gcongr`.

- **Theorem 4 / 5 proper.** Once the lemmas are in place, the
  partition-sum split at $K = X^{(c-1)/c}$ (or $K \asymp \sqrt{X/f(\sqrt X)}$
  for Theorem 5) plus elementary tail estimates closes the proof.
  These are standard `linarith` / `bound` style calculations.

The structure of the file deliberately mirrors `proofs/erdos_1194_note.tex`
to make the proof-port mechanical.
