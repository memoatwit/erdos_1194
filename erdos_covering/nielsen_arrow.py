"""
Utilities for Nielsen's arrow notation in the minimum-modulus-40 construction.

This is not yet the full Section 4 grammar. It implements finite expansion of
small arrow examples using an auxiliary integer `p`, matching Nielsen's worked
examples.

For `m=1`, `n=5`, `p=5`, this reproduces the paper's displayed `2^up` cover:

  1 mod 2, 2 mod 4, 4 mod 8, 8 mod 16, 16 mod 32,
  96 mod 160, 32 mod 80, 8 mod 40, 4 mod 20, 0 mod 10.

It also expands the Section 3 example `3^up(1, 2^up)`, which has 49
congruence classes when both arrows use auxiliary `p=5` and the binary arrow
is taken to depth `n=5`.
"""
from __future__ import annotations

import argparse
import json
import math
from dataclasses import asdict

from verify_covering import Congruence, validate_system, verify_coverage


UNIT = [Congruence(0, 1)]


def egcd(a: int, b: int) -> tuple[int, int, int]:
    if b == 0:
        return (a, 1, 0)
    g, x1, y1 = egcd(b, a % b)
    return (g, y1, x1 - (a // b) * y1)


def crt_pair(a1: int, m1: int, a2: int, m2: int) -> Congruence:
    """Solve x = a1 mod m1, x = a2 mod m2 for coprime moduli."""
    if m1 == 1:
        return Congruence(a2, m2).normalized()
    if m2 == 1:
        return Congruence(a1, m1).normalized()
    g, u, _ = egcd(m1, m2)
    if g != 1:
        raise ValueError(f"CRT moduli must be coprime, got {m1}, {m2}")
    modulus = m1 * m2
    x = (a1 + ((a2 - a1) * u % m2) * m1) % modulus
    return Congruence(x, modulus).normalized()


def intersect_system(base: Congruence, system: list[Congruence]) -> list[Congruence]:
    """Intersect one congruence with every congruence in a nested input."""
    return [
        crt_pair(base.residue, base.modulus, nested.residue, nested.modulus)
        for nested in system
    ]


def arrow_input_branch(q: int, m: int, branch_rep: int, input_index: int, k: int) -> Congruence:
    """Return the kth-level branch for the jth input of `(q^m)^up`.

    Nielsen's formula is

        a + j q^(k-1) - q^(m-1) (mod q^k),   k >= m.
    """
    if not (1 <= input_index <= q - 1):
        raise ValueError(f"input index must be in 1..{q - 1}")
    if k < m:
        raise ValueError("level k must be at least m")
    base = q ** (m - 1)
    modulus = q ** k
    residue = branch_rep + input_index * (q ** (k - 1)) - base
    return Congruence(residue, modulus).normalized()


def arrow_last_hole_branch(q: int, m: int, branch_rep: int, exponent: int) -> Congruence:
    """Return the continuing hole branch reduced modulo `q^exponent`."""
    if exponent == 0:
        return Congruence(0, 1)
    base = q ** (m - 1)
    modulus = q ** exponent
    return Congruence(branch_rep - base, modulus).normalized()


def q_arrow(
    q: int,
    m: int,
    n: int,
    p: int,
    inputs: list[list[Congruence] | None],
    branch: int | None = None,
) -> list[Congruence]:
    """Finite expansion of `(q^m)^up(inputs...)`.

    `inputs` has length `q-1`. Each non-None input is a finite congruence
    system to intersect with that input branch. Use `UNIT` for a plain filled
    branch. `None` means the input is left empty.

    The final continuing hole at depth `n` is closed with auxiliary modulus
    `p`, using the CRT filler in Nielsen's examples.
    """
    if q < 2:
        raise ValueError("q must be at least 2")
    if m < 1:
        raise ValueError("m must be at least 1")
    if n < m:
        raise ValueError("n must be at least m")
    if n < p - 1:
        raise ValueError("Nielsen's finite filler requires n >= p-1")
    if len(inputs) != q - 1:
        raise ValueError(f"expected {q - 1} inputs, got {len(inputs)}")
    if math.gcd(p, q) != 1:
        raise ValueError("p must be relatively prime to q")

    branch_rep = 1 if branch is None and m == 1 else branch
    if branch_rep is None:
        raise ValueError("branch must be supplied when m > 1")

    out: list[Congruence] = []
    for k in range(m, n + 1):
        for input_index, nested in enumerate(inputs, start=1):
            if nested is None:
                continue
            base_branch = arrow_input_branch(q, m, branch_rep, input_index, k)
            out.extend(intersect_system(base_branch, nested))

    for i in range(1, p + 1):
        exponent = n + 1 - i
        if exponent < 0:
            raise ValueError("final filler exponent became negative; choose larger n")
        q_branch = arrow_last_hole_branch(q, m, branch_rep, exponent)
        out.append(crt_pair(i % p, p, q_branch.residue, q_branch.modulus))

    return out


def binary_arrow(m: int, n: int, p: int, branch: int | None = None) -> list[Congruence]:
    """Finite expansion of `(2^m)^up`."""
    return q_arrow(2, m, n, p, [UNIT], branch)


def example_3_up_1_2_up() -> list[Congruence]:
    """Nielsen Section 3 example S = 3^up(1, 2^up), using p=5."""
    c = binary_arrow(m=1, n=5, p=5)
    return q_arrow(3, m=1, n=4, p=5, inputs=[UNIT, c])


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--example", choices=["2up", "3up_1_2up"], default="2up")
    parser.add_argument("--m", type=int, default=1)
    parser.add_argument("--n", type=int, default=5)
    parser.add_argument("--p", type=int, default=5)
    parser.add_argument("--branch", type=int, default=None)
    parser.add_argument("--verify", action="store_true")
    args = parser.parse_args()

    if args.example == "2up":
        congruences = binary_arrow(args.m, args.n, args.p, args.branch)
    else:
        congruences = example_3_up_1_2_up()

    data = {
        "example": args.example,
        "congruence_count": len(congruences),
        "congruences": [asdict(c) for c in congruences],
    }
    if args.example == "2up":
        data.update({"m": args.m, "n": args.n, "p": args.p, "branch": args.branch})
    if args.verify:
        metadata = validate_system(congruences, require_distinct=True)
        period = math.lcm(*(c.modulus for c in congruences))
        data["system"] = metadata
        data["coverage"] = verify_coverage(congruences, period, chunk_size=period)
    print(json.dumps(data, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
