# Erdős covering systems — minimum modulus attack

## Problem (Erdős 1950, partially solved 2015)

A **covering system** is a finite set of arithmetic progressions
`{a_i mod n_i}` whose union is `Z`.  A covering system is called
**distinct** (or "exact") if all `n_i` are different.

Erdős's question: can the minimum modulus `min_i n_i` of a distinct
covering system be arbitrarily large?

Hough (2015) proved no: `min_i n_i ≤ 10^16` always.  Balister-Bollobás-Morris-
Sahasrabudhe-Tiba (2022) reduced this to 616,000.

**The constructive side is wide open.**  Current explicit record:

- Nielsen (2009): min modulus 40.  System has ~10^7 congruences.
- Owens (~2014): min modulus 42.

The minimum-modulus problem upper bound has a multi-orders-of-magnitude gap
between known constructions (42) and theoretical limit (616,000).

**Win condition for this attack:** an explicit distinct-modulus covering
system with min modulus ≥ 43, verified by `verify_covering.py`.

## Plan

1. **Verifier** (`verify_covering.py`): takes a JSON list of `[a, n]` pairs,
   confirms moduli are distinct, computes `min`, `max`, `L = lcm(n_i)`,
   and checks `∪ {a_i + k n_i : k} ⊇ Z` by simulating `[0, L)`.

2. **Reproduce Nielsen-style baseline.**  Nielsen's idea: a *primorial*
   skeleton `M = 2·3·5·7·11·13·17·19·23` and place congruences inside `Z/M`.
   Moduli are divisors of `M` with `n_i ≥ 40`.  Use a recursive block decomp:
   first cover all residues `mod 2`, then those uncovered `mod 6`, then
   `mod 30`, etc., picking only moduli ≥ 40 at each step.

3. **Push to 43.**  Replace the smallest moduli (40, 41, 42) by larger ones
   or by combinations of larger moduli that achieve the same coverage.

4. **Independent verification.**  Once a candidate is found, verify by
   computing the uncovered set mod `lcm` and confirming it's empty.

## Files

- `verify_covering.py` — independent verifier.
- `cover_search.py` — DFS / SAT / ILP search infrastructure.
- `nielsen_baseline.py` — implements Nielsen-style construction for
  baseline tests at min modulus 40.
- `results/` — JSON output of candidate covers.
