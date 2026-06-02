# Covering Systems

Goal: independently reconstruct and verify a distinct covering system with
minimum modulus 40, following Nielsen's 2009 construction before attempting
anything record-facing.

## Current Facts

- Nielsen constructed a distinct covering system with smallest modulus 40.
- Owens later constructed one with minimum modulus 42.
- Hough proved the minimum modulus in a distinct covering system is bounded
  above by `10^16`, so the original unboundedness question is closed.
- Nielsen's construction is not practical to expand as a flat congruence list:
  using the auxiliary prime `p=107`, the paper estimates more than `10^50`
  congruence classes.  Reproduction therefore needs symbolic verification of
  the arrow/tree construction.

## Local Verifier

`verify_covering.py` checks a finite list of congruences
`residue (mod modulus)`.

For small systems it computes the exact lcm period automatically.  For large
recursive systems it can verify against a supplied period in bounded chunks,
provided every modulus divides that period.

Examples:

```bash
python3 erdos_covering/verify_covering.py \
  erdos_covering/examples/erdos_5.json \
  --overlap-stats

python3 erdos_covering/verify_covering.py \
  erdos_covering/examples/not_covering.json
```

## Next Steps

1. Extend the Section 4 symbolic encoding prime by prime.
2. Track holes/inputs symbolically and verify that every empty input is filled.
3. Keep using finite expansion only for tiny worked examples.

## Nielsen Arrow Prototype

`nielsen_arrow.py` currently implements finite expansion for Nielsen arrows
`(q^m)^up(inputs...)`, plus the binary convenience wrapper `(2^m)^up`.

The smoke test below reproduces Nielsen's worked `2^up` example with `p=5`,
`n=5`, including the congruences `96 mod 160`, `32 mod 80`, `8 mod 40`,
`4 mod 20`, and `0 mod 10`.

```bash
python3 erdos_covering/nielsen_arrow.py --example 2up --m 1 --n 5 --p 5 --verify
```

The second smoke test expands the Section 3 example `3^up(1, 2^up)` using
the same finite auxiliary choice `p=5`.  It produces 49 congruence classes
with distinct moduli and verifies coverage over its lcm period.

```bash
python3 erdos_covering/nielsen_arrow.py --example 3up_1_2up --verify
```

## Symbolic Modulus Prototype

`nielsen_symbolic.py` tracks modulus families as prime-exponent constraints.
For example, Nielsen says `5^up(1, 2, 4, 3^up(1, 2^up))` uses exactly
families of the form `5^a`, `5^a 2`, `5^a 4`, `5^a 3^b`, and
`5^a 3^b 2^c`, with positive arrow exponents.  The symbolic checker now
reproduces that and checks that the families are disjoint.

```bash
python3 erdos_covering/nielsen_symbolic.py --example paper_sample
```

It also encodes the first construction moves from Subsections 4.1-4.3,
including the removal of moduli `2,4,8,16,32` and `6,12,18,24,36`.
This first symbolic pass has 19 modulus families, minimum symbolic modulus
`40`, and no detected collisions.

```bash
python3 erdos_covering/nielsen_symbolic.py --example section4_initial
```

Subsection 4.4, the prime `7`, is now encoded separately and in combination
with the earlier moves.  The combined 4.1-4.4 symbolic modulus report has 74
families, minimum symbolic modulus `40`, and no detected collisions.

```bash
python3 erdos_covering/nielsen_symbolic.py --example section4_4
python3 erdos_covering/nielsen_symbolic.py --example section4_through_4_4
```

There is also a coverage-slot report for Subsection 4.4.  This is deliberately
separate from modulus bookkeeping: blank inputs become open holes, while
Nielsen's `x` entries are counted as already-filled slots and do not create new
modulus families.

```bash
python3 erdos_covering/nielsen_symbolic.py --example section4_4_coverage
```

Subsection 4.5, the prime `11`, is now encoded.  It fills the holes from
moduli `6` and `18` on the `1 (mod 4)` branch.  All 10 inputs of the `11^up`
are filled (Nielsen states explicitly that no new holes are introduced).
Section 4.5 alone has 65 families with min symbolic modulus `44 = 11 * 4`.

```bash
python3 erdos_covering/nielsen_symbolic.py --example section4_5
python3 erdos_covering/nielsen_symbolic.py --example section4_5_coverage
```

The combined check through Subsection 4.5 has 139 modulus families, minimum
symbolic modulus `40`, and no detected collisions.

```bash
python3 erdos_covering/nielsen_symbolic.py --example section4_through_4_5
```

Subsection 4.6, the prime `13`, is partially encoded.  The `13^up` has 12
inputs: the first 10 mirror 4.5's `11^up` inputs, and the last two are
modified `11^up`'s on the `3 (mod 4)` branch (with `4`/`8^up` substitutions).
Section 4.6 alone has 163 families and minimum symbolic modulus `52 = 13 * 4`.

```bash
python3 erdos_covering/nielsen_symbolic.py --example section4_6
python3 erdos_covering/nielsen_symbolic.py --example section4_through_4_6
```

The combined check through 4.6 has 302 modulus families and minimum
symbolic modulus `40`, but reports 91 internal collisions.  These are NOT
bugs.  Nielsen distinguishes inputs 11 and 12 of the `13^up` by a
*residue-level* substitution (`put an x on any entry ending in 20 or 21`)
that the current modulus-only bookkeeping cannot represent.  Resolving the
collisions requires adding residue tracking to `Pattern`/`PatternSet`; see
`nielsen_reconstruction.md` "Next Technical Step".
