# Erdős r_3(N) — exact max-size 3-AP-free subset of {1..N}

## Paper and artifacts

- Preprint: [arXiv:2606.04016](https://arxiv.org/abs/2606.04016)
- Dataset: [Zenodo 10.5281/zenodo.20463334](https://doi.org/10.5281/zenodo.20463334)
- Maintained manuscript: [`paper/paper.tex`](paper/paper.tex) and
  [`paper/paper.body.tex`](paper/paper.body.tex)
- Venue and follow-up plan: [`paper/VENUE_AND_EXPERIMENT_PLAN.md`](paper/VENUE_AND_EXPERIMENT_PLAN.md)
- Claim-to-artifact verification guide: [`ARTIFACT_REPRODUCIBILITY.md`](ARTIFACT_REPRODUCIBILITY.md)

Current result snapshot:

- All 18 chunks closed by the initial PySAT/CaDiCaL configuration and both
  historical T1c chunks have independently verified DRAT proofs.
- On byte-identical T1b formulas, native CaDiCaL 3.0.0 and kissat 4.0.4 both
  close 20/20. The original T1c solvability gap was an invocation/configuration
  effect, not a persistent solver separation.
- A full no-proof T2 portfolio closes 6,045/6,071 chunks (99.57%): kissat
  closes 5,959, then native CaDiCaL closes 86 of the 112 residuals. No SAT row
  appears; 26 chunks remain unresolved.
- Exact regressions at `N=80,90,100` combine independently verified lower
  witnesses with Kissat DRAT proofs, DRAT-to-LRAT conversion, and formally
  verified `cake_lpr` checking.
- A standard-library model audit independently reproduces 11,130 AP
  constraints and 22,154 active window inequalities and records SHA-256
  digests for the source b-file and generated high-level model.
- The deployed depth-24 split is witness-anchored numeric order. A later code
  audit found that the generic set loader normalized the stored degree order;
  the exact deployed 24-value prefix is documented in the manuscript and
  released outputs.
- A matched five-policy ablation over 500 raw assignments reproduces the
  historical 12,582,912-cube cover and finds a complete global AP-degree
  cover with 96,847 survivors. Those survivors are harder at the 60-second
  CP-SAT cap, so the result is a cover-size/hardness tradeoff rather than a
  claimed 130-fold runtime speedup.

The full `r_3(212)` upper bound remains open because the complete T3 cube
space has not been certified.

```bibtex
@misc{ergezer-r3-212-2026,
  author        = {Ergezer, Mehmet},
  title         = {Salem--Spencer sets as a cross-solver benchmark:
                   decomposition, certification, and split-policy effects
                   at $r_3(212)$},
  year          = {2026},
  eprint        = {2606.04016},
  archivePrefix = {arXiv},
  primaryClass  = {math.CO}
}
```

## Problem

For each positive integer N, let

    r_3(N) = max { |A| : A ⊂ {1, ..., N}, A contains no 3-term arithmetic progression }.

Equivalently, A is *3-AP-free* if there is no triple `a < b < c` in A with
`b - a = c - b`, i.e. `a + c = 2b`.

The sequence `(r_3(N))_{N >= 1}` is OEIS [A003002].  Known exact values:

- A003002 b-file (Cariboni): n = 0..211.
- Frontier: n = 211 with r_3(211) = 43.
- Related threshold sequence A065825 currently gives a(43) = 209; the next
  unknown threshold is a(44).
- No extension beyond n = 211 is listed in the OEIS b-file as of 2026-07-12.

The asymptotic side of r_3(N) is governed by the Bloom-Sisask, Kelley-Meka,
and subsequent advances; these don't compute exact small values.

## Win condition

An exact value of r_3(N) for some N >= 212, with:

1. an explicit witness A ⊆ {1..N} of size r_3(N) (lower bound),
2. an independent proof that no A' ⊆ {1..N} of size r_3(N) + 1 is 3-AP-free
   (upper bound).

Both halves verified by `r3_verify.py` and ideally by a second method
(SAT vs. exact DFS, or two different solvers).

## Plan

1. **r3_verify.py** — independent verifier.
   - Read a list of integers; check they are distinct, in [1..N], and 3-AP-free.
   - Output: size and pass/fail.
2. **r3_brute.py** — reference exact DFS.
   - Backtracking by element-at-a-time.
   - Validate against OEIS A003002 b-file up to some N where brute is fast (~30-40).
3. **r3_milp.py** — exact MILP encoding using SciPy/HiGHS.
   - Boolean x_i for i in [1..N].  Maximize sum x_i.
   - For each AP (a, b, c) in [1..N]: constraint x_a + x_b + x_c <= 2.
   - Symmetry breaking: i <-> N+1-i reflection, fix x_1 >= x_N.
   - Useful as an independent exact cross-check, but slow by N≈50.
4. **r3_cpsat.py** — CP-SAT encoding using OR-Tools.
   - Same Boolean/AP model as MILP.
   - Loads local dependencies from `erdos_r3/.deps` if OR-Tools is not
     globally installed.
   - Supports fixed variables, solution hints, decision mode, and full JSON
     save output.
5. **r3_random_greedy.py** — lower-bound witness finder.
   - Randomized fixed-cardinality repair search.
   - Used to save a verified 43-point witness for N=212.
6. **r3_split_cpsat.py** — resumable upper-bound runner.
   - Splits fixed-cardinality CP-SAT decisions into JSONL chunks.
   - Supports endpoint-pair and high-incidence variable split strategies.
7. **results/** — JSON/JSONL per N with witnesses, chunk status, and runtime.

## Cross-checks

- Certified exact regressions at `N=80,90,100` match OEIS A003002. Both the
  lower witness and the size-plus-one upper-bound certificate are checked.
- Reflection invariance: r_3(N) = r_3 of the reflected set i -> N+1-i.
- A new value is published with an OEIS-ready triple (n, size, witness).
- `python r3_model_audit.py` regenerates and hashes the high-level
  `N=212`, `K=44` constraint families without importing solver code.

## References

- OEIS A003002, https://oeis.org/A003002
- Salem-Spencer (1942), constructed sets of size N^{1-o(1)} that are 3-AP-free.
- Behrend (1946), sharper construction.
- Bloom-Sisask, Kelley-Meka (2023+), asymptotic upper bounds.
