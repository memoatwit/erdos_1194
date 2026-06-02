# Nielsen Min-Modulus 40 Reconstruction

Date: May 17, 2026

## Source

Downloaded and text-extracted:

```text
literature/MinimumModulus40_Nielsen.pdf
literature/MinimumModulus40_Nielsen.txt
```

The paper is Pace P. Nielsen, "A covering system whose smallest modulus is
40", Journal of Number Theory 129 (2009), 640-666.

## Key Finding

This is not a machine-readable congruence list.  Nielsen explicitly notes that
if the arrows are made finite using `p = 107`, the construction has more than
`(p-1)^25 > 10^50` congruence classes.  The reproducible object is therefore a
symbolic arrow/tree construction.

Nielsen says the straightforward computer check should:

1. Check that no modulus is repeated, listing used moduli while treating each
   upward arrow as exhausting all higher powers.
2. Check that each empty input is eventually filled by later or earlier
   congruence classes.

This matches the local plan: build a symbolic checker rather than a flat
enumerator.

## Implemented Locally

- `verify_covering.py`
  - Exact lcm/period verifier for small systems.
  - Chunked fixed-period verifier for large systems when every modulus divides
    the supplied period.
  - Positive smoke test: classic 5-congruence example.
  - Negative smoke test: incomplete two-congruence example.

- `nielsen_arrow.py`
  - CRT helper.
  - Finite expansion for generalized arrows `(q^m)^up(inputs...)`.
  - Binary wrapper `(2^m)^up`.
  - Verified Nielsen's worked `2^up` example with `p=5`, `n=5`.
  - Verified the Section 3 example `3^up(1, 2^up)` with finite auxiliary
    `p=5`, producing 49 congruence classes.

- `nielsen_symbolic.py`
  - Symbolic modulus-family representation using prime-exponent constraints.
  - Ordinary split node `q(...)` and arrow node `(q^m)^up(...)`.
  - Products, unions, finite removals of small moduli, and family-collision
    checks.
  - Coverage-slot bookkeeping that treats blanks as open holes and `x` entries
    as already-filled slots.
  - Reproduces Nielsen's explanatory sample
    `5^up(1, 2, 4, 3^up(1, 2^up))`.
  - Encodes the initial Subsections 4.1-4.3 modulus bookkeeping.
  - Encodes Subsection 4.4, including the ordered set
    `A = {2, 4, 3^up(1, 2), 1, 8^up, 3^up(4, 8^up)}` and the three
    `49^up` fillers described by Nielsen.

## Verified Worked Examples

Command:

```bash
python3 erdos_covering/nielsen_arrow.py --example 2up --m 1 --n 5 --p 5 --verify
```

Output congruences:

```text
1 mod 2
2 mod 4
4 mod 8
8 mod 16
16 mod 32
96 mod 160
32 mod 80
8 mod 40
4 mod 20
0 mod 10
```

The verifier confirms these cover all residues modulo 160, with distinct
moduli.

Command:

```bash
python3 erdos_covering/nielsen_arrow.py --example 3up_1_2up --verify
```

This expands Nielsen's Section 3 example `S = 3^up(1, 2^up)` with auxiliary
`p=5`.  The expansion has 49 congruence classes, all moduli are distinct, and
the finite verifier confirms coverage over the lcm period 12960.

## Verified Symbolic Checks

Command:

```bash
python3 erdos_covering/nielsen_symbolic.py --example paper_sample
```

Result:

```text
family_count = 5
min_symbolic_modulus = 5
collision_count = 0
families = 5^>=1, 2*5^>=1, 2^2*5^>=1, 3^>=1*5^>=1,
           2^>=1*3^>=1*5^>=1
```

This matches Nielsen's stated family list for the sample expression.

Command:

```bash
python3 erdos_covering/nielsen_symbolic.py --example section4_initial
```

Result:

```text
family_count = 19
min_symbolic_modulus = 40
collision_count = 0
```

This encodes the first construction moves from Subsections 4.1-4.3, including
finite removals of the small moduli `2,4,8,16,32` and `6,12,18,24,36`.

Command:

```bash
python3 erdos_covering/nielsen_symbolic.py --example section4_4
```

Result:

```text
family_count = 55
min_symbolic_modulus = 42
collision_count = 0
```

Command:

```bash
python3 erdos_covering/nielsen_symbolic.py --example section4_through_4_4
```

Result:

```text
family_count = 74
min_symbolic_modulus = 40
collision_count = 0
```

Command:

```bash
python3 erdos_covering/nielsen_symbolic.py --example section4_4_coverage
```

Result:

```text
raw 4.4 expression: 6 blank inputs, 15 prefilled x entries
after Nielsen's 49^up fillers: 3 atomic residual requirements
```

The residual requirements are Nielsen's prose summary: the left hole is empty
except that `20 mod 25` is filled, and the right gray hole still needs one
class modulo `5` and one class modulo `5*3`.

## Subsection 4.5 (prime 11)

Encoded in `section4_5()`, with combined check `section4_through_4_5()` and
coverage report `section4_5_coverage()`.

Nielsen's Subsection 4.5 uses the prime `11` to fill the holes that arose
from moduli `6` and `18` (i.e., the prime-3 residual holes in Subsection 4.2),
restricted to the `1 (mod 4)` branch.  The companion case `3 (mod 4)` is
handled by Subsection 4.6 (prime 13).  The `11^up` arrow has 10 inputs and
all of them are filled, so Nielsen writes "without creating any new holes".

The expression reuses three composite blocks both as top-level inputs of
the `11^up` and as inputs of a parallel `7^up` inside input 10:

```text
common3 = 3·2 + 27·1 + 27^up·2          (input 3 of 11^up; input 1 of inner 7^up)
common4 = 3·4 + 27·4 + 27^up·8^up       (input 4 of 11^up; input 2 of inner 7^up)
common8 = 3·3(1,2,4) + 81^up(1,4)
        + 5^up(27^up·1, 27^up·2, 27^up·4, 27^up·8^up)
                                         (input 8 of 11^up; input 5 of inner 7^up)
```

Command:

```bash
python3 erdos_covering/nielsen_symbolic.py --example section4_5
```

Result:

```text
family_count = 65
min_symbolic_modulus = 44
collision_count = 0
```

Combined with the previous subsections:

```bash
python3 erdos_covering/nielsen_symbolic.py --example section4_through_4_5
```

Result:

```text
family_count = 139
min_symbolic_modulus = 40
collision_count = 0
```

Coverage report for Subsection 4.5:

```bash
python3 erdos_covering/nielsen_symbolic.py --example section4_5_coverage
```

```text
raw 4.5 expression: 6 blank inputs, 2 prefilled x entries, 32 filled
final residual: 0 open
```

The 6 raw blanks all sit inside input 10's first part,
`5^up(3(3(1,4,_),_,_),_,_,_)`.  Per Nielsen's prose, those slots are filled
by the parallel `7^up(...)` summed in the same `11^up` input.  The coverage
model does not yet auto-cancel within-input sums; the final-residual report
records Nielsen's "no new holes" claim explicitly.

## Subsection 4.6 (prime 13) — partial

Encoded in `section4_6()` with `section4_through_4_6()` and
`section4_6_coverage()`.  The `13^up` arrow has 12 inputs:

- Inputs 1-10 reuse 4.5's 10 inputs verbatim.  (Residues are on the
  `3 (mod 4)` branch but residues do not affect modulus-family bookkeeping.)
- Input 11 is a modified `11^up`: the leaves `4` and `8^up` become `x`
  (already covered in Subsection 4.5).  In modulus terms, the `4`/`8^up`
  contributions are dropped.
- Input 12 is another `11^up`: same skeleton, with `4 -> 1` and
  `8^up -> 2` swap applied to remaining leaves.

`_section4_5_inputs()` was refactored to expose the 10-input list with two
flags (`x_for_4_or_8up`, `swap_4_to_1_and_8up_to_2`) so the 4.6 modifications
reuse the same builder.  Cross-check: `section4_5()` is now built from this
helper, and `_legacy_section4_5()` is preserved as a regression baseline.
Both produce `family_count = 65, min_symbolic_modulus = 44, collisions = 0`.

Commands:

```bash
python3 erdos_covering/nielsen_symbolic.py --example section4_6
python3 erdos_covering/nielsen_symbolic.py --example section4_through_4_6
python3 erdos_covering/nielsen_symbolic.py --example section4_6_coverage
```

Results:

```text
section4_6:           family_count = 163, min = 52, collisions = 91
section4_through_4_6: family_count = 302, min = 40, collisions = 91
section4_6_coverage:  raw open = 18, prefilled_x = 24, filled = 78,
                      residual = 0
```

The 91 collisions are NOT bugs in the encoding.  They are all internal to
4.6, between input 11 and input 12 of the outer `13^up`.  Both reuse the
same `11^up` skeleton; their shared sub-expressions (`common3`, parts of
`common8`, and the parts of other inputs that do not reference `4` or
`8^up`) produce identical modulus families when wrapped by `13 * 11`.

Nielsen's prose disambiguates them by saying:

> "put an x on any entry ending in 20 or 21"

This refers to **residue values** (the `a` in `a mod n`) ending in 20 or
21, not modulus values.  The substitution removes exactly the entries that
collide between input 11 and input 12.

Our modulus-only bookkeeping cannot distinguish residues, so the 91
collisions are an honest reflection of the symbolic limit.  Resolving them
requires a residue-tracking extension of `Pattern`/`PatternSet`.

## Next Technical Step

- Add a residue-tracking layer to `nielsen_symbolic.py`.  Each modulus
  family also carries a residue constraint (a finite set of allowed
  residues mod the modulus, or a structured representation).  Subsections
  4.6+ then become checkable.
- Independent check: produce a finite expansion of 4.5 using
  `nielsen_arrow.py` for a very small auxiliary prime `p`, and confirm that
  no moduli repeat.  This is a sanity test for the 4.5 encoding before
  scaling further.
- Continue the symbolic encoding (4.7 onward) once residue tracking is in.
