# Erdős r_3(N) — exact max-size 3-AP-free subset of {1..N}

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
- No more recent computational extensions reported in 2024-2025.

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

- For N <= 100: r_3(N) must match OEIS A003002.  Both witness and infeasibility
  at size+1 confirmed.
- Reflection invariance: r_3(N) = r_3 of the reflected set i -> N+1-i.
- A new value is published with an OEIS-ready triple (n, size, witness).

## References

- OEIS A003002, https://oeis.org/A003002
- Salem-Spencer (1942), constructed sets of size N^{1-o(1)} that are 3-AP-free.
- Behrend (1946), sharper construction.
- Bloom-Sisask, Kelley-Meka (2023+), asymptotic upper bounds.
