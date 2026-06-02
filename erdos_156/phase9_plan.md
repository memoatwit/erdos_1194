# Phase 9 — Erdős Problem #156 attack

## Problem

Erdős Problem #156 asks:

> Does there exist a maximal Sidon set \(A \subset \{1,\ldots,N\}\) of size
> \(O(N^{1/3})\)?

Here **maximal** means inclusion-maximal inside \([1,N]\): \(A\) is Sidon and
no element of \([1,N]\setminus A\) can be added while preserving the Sidon
property.

Source: https://www.erdosproblems.com/156, accessed 2026-05-14.

## Current public status

- Status on erdosproblems.com: **OPEN**.
- Comment thread: **0 comments** as of 2026-05-14.
- Recorded bounds:
  - Greedy maximal Sidon sets have size \(\gg N^{1/3}\).
  - Ruzsa [Ru98b] constructed maximal Sidon sets of size
    \(\ll (N\log N)^{1/3}\).
- Goal: close the logarithmic gap by constructing maximal Sidon sets of size
  \(O(N^{1/3})\), or find evidence/obstructions suggesting the log factor is
  real.

## Why this is the next target

We pivoted here after checking #42/#43:

- #42 is now marked solved on erdosproblems.com.
- #43 is now marked disproved.
- The local `erdos_42/` work is still useful as a CP-SAT verification harness,
  but it is no longer a promising route to a new Erdős-problem solution.

Problem #156 is still quiet, open, and structurally close to our existing toolkit:
Sidon constraints, maximality/extension constraints, exact small-\(N\)
optimization, and greedy/construction experiments.

## Finite optimization target

Define

\[
m(N) := \min \{|A| : A\subset [1,N],\ A \text{ is Sidon and maximal in }[1,N]\}.
\]

The Erdős problem asks whether \(m(N) = O(N^{1/3})\).
Known constructions give \(m(N) \ll (N\log N)^{1/3}\), while the easy lower
bound gives \(m(N) \gg N^{1/3}\).

The first computational task is to compute exact \(m(N)\) for modest \(N\),
then compare:

- \(m(N)/N^{1/3}\)
- \(m(N)/(N\log N)^{1/3}\)
- witness structure: gaps, occupied residues, covered/blocked positions

## CP-SAT formulation

Variables:

- \(y_i \in \{0,1\}\) for \(i\in[1,N]\), indicating \(i\in A\).
- \(u_{i,j}\in\{0,1\}\) for \(1\le i<j\le N\), encoding \(y_i\wedge y_j\).

Sidon constraints:

- For every positive difference \(d\),
  \[
  \sum_{1\le i\le N-d} u_{i,i+d} \le 1.
  \]

Maximality constraints:

For every \(x\in[1,N]\), either \(x\in A\), or adding \(x\) creates a duplicate
positive difference. Equivalently, if \(y_x=0\), then at least one of the
following blockers must occur:

1. **Existing-difference blocker:** for some \(a\in A\), the difference
   \(|x-a|\) is already used by a pair in \(A\).
2. **Symmetric-new-difference blocker:** for distinct \(a,a'\in A\),
   \(|x-a|=|x-a'|\), i.e. \(a+a'=2x\).

Implementation options:

- Direct CP-SAT with auxiliary blocker Booleans for each \(x\).
- Faster custom DFS using difference bitsets:
  - Maintain `A`, `used_diffs`.
  - Candidate `x` is addable iff all new diffs `abs(x-a)` are distinct and
    disjoint from `used_diffs`.
  - Maximality means no outside `x` is addable.

Objective:

\[
\min \sum_{i=1}^N y_i.
\]

## Immediate implementation plan

1. Create `erdos_156/solve_156.py`.
2. Implement:
   - `is_sidon(A, N=None)`
   - `is_maximal_sidon(A, N)`
   - greedy builders for quick upper bounds
   - CP-SAT exact solver for \(m(N)\)
3. Run exact computations for small \(N\), starting with:
   \[
   N = 10,15,20,25,30,35,40,50.
   \]
4. Save results to:
   - `erdos_156/results/exact_156.json`
   - `erdos_156/results/exact_156_summary.md`
5. Inspect witnesses manually and look for a reusable construction pattern.

## First things to watch

- Does exact \(m(N)\) track \(cN^{1/3}\) with a stable constant?
- Do optimal witnesses look random-greedy, modular, interval-blocked, or
  structured by residue classes?
- How many outside points are blocked by existing differences versus by
  symmetric-new-difference collisions?
- Are small exact witnesses extendable into larger maximal witnesses, or is
  there an extension-cost trap like in #1194 finite optima?

## Possible analytic routes

### Construction route

Try to derandomize or sharpen Ruzsa's construction. If the log factor comes
from a union bound, search for a Lovasz-local-lemma or nibble-style improvement.

### Blocking route

A maximal Sidon set \(A\) must block every \(x\notin A\). Each blocker is a
local equation involving \(x\) and either:

- one existing difference from \(A-A\), or
- a symmetric pair around \(x\).

If a set of size \(C N^{1/3}\) can cover all \(x\) by these blockers while
remaining Sidon, that gives the desired construction.

### Computational-to-theorem route

Use exact witnesses to infer an explicit family, then prove:

1. the family is Sidon;
2. every outside \(x\in[1,N]\) is blocked;
3. the family has \(O(N^{1/3})\) elements.

## Stop conditions for session 1

Session 1 should be considered successful if it produces:

- a correct verifier for Sidon and maximal Sidon sets;
- an exact or trusted CP-SAT model for \(m(N)\);
- the first table of exact values/witnesses;
- a short summary of what the witnesses look like.

Do not claim progress on the Erdős problem from finite data alone. The value of
the computation is to locate structure or falsify naive construction ideas.

## Session 1 status

Done. See `phase9_summary.md`.

Because `ortools` is not installed in this workspace, the first implementation
uses a self-contained bitset DFS rather than CP-SAT. It solved
\(N=5,10,\ldots,60\) exactly and timed out at the first hard case \(N=65\),
where it proved no size-5 solution and left \(m(65)\in\{6,7\}\).
