"""
Symbolic modulus bookkeeping for Nielsen's minimum-modulus-40 construction.

The full construction is too large to expand as congruence classes.  Nielsen's
suggested check is symbolic: record which moduli are used, treating each arrow
as all sufficiently high powers of its prime, and separately check that empty
inputs are eventually filled.

This module implements the first half of that check.  It models families such
as

    5^a * 3^b * 2^c,  with a,b,c >= 1

as exponent constraints, supports ordinary splits q(...), arrows (q^m)^up(...),
products, unions, finite removals of small moduli, and pairwise collision tests.
It also contains a small coverage-slot model for tracking blanks versus
Nielsen's `x` entries, which mean an input is already filled by earlier work.
"""
from __future__ import annotations

import argparse
import itertools
import json
import math
from dataclasses import dataclass
from functools import reduce
from typing import Iterable


@dataclass(frozen=True, order=True)
class Exp:
    """A prime exponent constraint: exact e, or e >= floor."""

    kind: str
    value: int

    def __post_init__(self) -> None:
        if self.kind not in {"exact", "ge"}:
            raise ValueError(f"bad exponent kind: {self.kind}")
        if self.value < 0:
            raise ValueError("exponents must be nonnegative")

    @staticmethod
    def exact(value: int) -> "Exp":
        return Exp("exact", value)

    @staticmethod
    def ge(value: int) -> "Exp":
        return Exp("ge", value)

    def add(self, other: "Exp") -> "Exp":
        if self.kind == "exact" and other.kind == "exact":
            return Exp.exact(self.value + other.value)
        return Exp.ge(self.value + other.value)

    def overlaps(self, other: "Exp") -> bool:
        if self.kind == "exact" and other.kind == "exact":
            return self.value == other.value
        if self.kind == "exact":
            return self.value >= other.value
        if other.kind == "exact":
            return other.value >= self.value
        return True

    def intersection_sample(self, other: "Exp") -> tuple[int, bool] | None:
        """Return one shared exponent and whether the intersection is infinite."""
        if not self.overlaps(other):
            return None
        if self.kind == "exact" and other.kind == "exact":
            return (self.value, False)
        if self.kind == "exact":
            return (self.value, False)
        if other.kind == "exact":
            return (other.value, False)
        return (max(self.value, other.value), True)

    def render(self) -> str:
        op = "=" if self.kind == "exact" else ">="
        return f"{op}{self.value}"


def factor(n: int) -> dict[int, int]:
    if n < 1:
        raise ValueError("only positive integers have modulus patterns")
    out: dict[int, int] = {}
    d = 2
    while d * d <= n:
        while n % d == 0:
            out[d] = out.get(d, 0) + 1
            n //= d
        d += 1 if d == 2 else 2
    if n > 1:
        out[n] = out.get(n, 0) + 1
    return out


def exact_vector(exponents: dict[int, int]) -> tuple[tuple[int, int], ...]:
    return tuple(sorted((p, e) for p, e in exponents.items() if e != 0))


def multiply_vectors(
    left: tuple[tuple[int, int], ...],
    right: tuple[tuple[int, int], ...],
) -> tuple[tuple[int, int], ...]:
    out: dict[int, int] = {}
    for p, e in left:
        out[p] = out.get(p, 0) + e
    for p, e in right:
        out[p] = out.get(p, 0) + e
    return exact_vector(out)


@dataclass(frozen=True)
class Pattern:
    constraints: tuple[tuple[int, Exp], ...]
    exclusions: frozenset[tuple[tuple[int, int], ...]] = frozenset()

    @staticmethod
    def one() -> "Pattern":
        return Pattern(())

    @staticmethod
    def from_int(n: int) -> "Pattern":
        return Pattern(tuple((p, Exp.exact(e)) for p, e in sorted(factor(n).items())))

    @staticmethod
    def arrow_power(q: int, m: int) -> "Pattern":
        if q < 2 or m < 1:
            raise ValueError("arrow prime and exponent floor must be positive")
        return Pattern(((q, Exp.ge(m)),))

    def constraint_map(self) -> dict[int, Exp]:
        return dict(self.constraints)

    def constraint_for(self, prime: int) -> Exp:
        return self.constraint_map().get(prime, Exp.exact(0))

    def multiply(self, other: "Pattern") -> "Pattern":
        left = self.constraint_map()
        right = other.constraint_map()
        primes = sorted(set(left) | set(right))
        merged = []
        for prime in primes:
            merged.append((prime, left.get(prime, Exp.exact(0)).add(right.get(prime, Exp.exact(0)))))

        exclusions = set()
        if self.exclusions:
            if not other.is_exact():
                raise ValueError("multiplying excluded families is only implemented by exact factors")
            other_vec = other.exact_exponents()
            exclusions.update(multiply_vectors(ex, other_vec) for ex in self.exclusions)
        if other.exclusions:
            if not self.is_exact():
                raise ValueError("multiplying excluded families is only implemented by exact factors")
            self_vec = self.exact_exponents()
            exclusions.update(multiply_vectors(self_vec, ex) for ex in other.exclusions)

        return Pattern(tuple(merged), frozenset(exclusions))

    def is_exact(self) -> bool:
        return all(exp.kind == "exact" for _, exp in self.constraints)

    def exact_exponents(self) -> tuple[tuple[int, int], ...]:
        if not self.is_exact():
            raise ValueError("pattern is not exact")
        return tuple((p, exp.value) for p, exp in self.constraints if exp.value)

    def contains_int(self, n: int) -> bool:
        vec = exact_vector(factor(n))
        if vec in self.exclusions:
            return False
        exponents = dict(vec)
        primes = set(exponents) | {p for p, _ in self.constraints}
        for prime in primes:
            value = exponents.get(prime, 0)
            constraint = self.constraint_for(prime)
            if constraint.kind == "exact" and value != constraint.value:
                return False
            if constraint.kind == "ge" and value < constraint.value:
                return False
        return True

    def exclude_int(self, n: int) -> "Pattern":
        if not self.contains_int(n):
            return self
        return Pattern(self.constraints, self.exclusions | {exact_vector(factor(n))})

    def overlaps(self, other: "Pattern") -> bool:
        primes = sorted({p for p, _ in self.constraints} | {p for p, _ in other.constraints})
        sample: dict[int, int] = {}
        infinite = False
        for prime in primes:
            shared = self.constraint_for(prime).intersection_sample(other.constraint_for(prime))
            if shared is None:
                return False
            value, is_infinite = shared
            sample[prime] = value
            infinite = infinite or is_infinite

        sample_vec = exact_vector(sample)
        if sample_vec not in self.exclusions and sample_vec not in other.exclusions:
            return True

        if not infinite:
            return False

        # Finite exclusions cannot remove an infinite intersection.  Search a
        # small box to produce a non-excluded witness before falling back.
        ge_primes = [
            p for p in primes
            if self.constraint_for(p).kind == "ge" and other.constraint_for(p).kind == "ge"
        ]
        for bumps in itertools.product(range(4), repeat=len(ge_primes)):
            candidate = dict(sample)
            for prime, bump in zip(ge_primes, bumps):
                candidate[prime] += bump
            vec = exact_vector(candidate)
            if vec not in self.exclusions and vec not in other.exclusions:
                return True
        return True

    def min_modulus(self, slack: int = 8) -> int | None:
        bases = {p: exp.value for p, exp in self.constraints}
        ge_primes = [p for p, exp in self.constraints if exp.kind == "ge"]
        exact_primes = [p for p, exp in self.constraints if exp.kind == "exact"]
        candidates = []
        for bumps in itertools.product(range(slack + 1), repeat=len(ge_primes)):
            exponents = dict(bases)
            for prime, bump in zip(ge_primes, bumps):
                exponents[prime] += bump
            vec = exact_vector(exponents)
            if vec in self.exclusions:
                continue
            if any(exponents.get(p, 0) != self.constraint_for(p).value for p in exact_primes):
                continue
            candidates.append(math.prod(p ** e for p, e in exponents.items()))
        return min(candidates) if candidates else None

    def render(self) -> str:
        if not self.constraints:
            text = "1"
        else:
            parts = []
            for prime, exp in self.constraints:
                if exp.kind == "exact":
                    parts.append(str(prime) if exp.value == 1 else f"{prime}^{exp.value}")
                else:
                    parts.append(f"{prime}^{exp.render()}")
            text = " * ".join(parts)
        if self.exclusions:
            removed = []
            for vec in sorted(self.exclusions):
                removed.append(str(math.prod(p ** e for p, e in vec)))
            text += " except {" + ", ".join(removed) + "}"
        return text


@dataclass(frozen=True)
class Family:
    label: str
    pattern: Pattern


@dataclass(frozen=True)
class PatternSet:
    families: tuple[Family, ...]

    @staticmethod
    def one(label: str = "1") -> "PatternSet":
        return PatternSet((Family(label, Pattern.one()),))

    @staticmethod
    def integer(n: int, label: str | None = None) -> "PatternSet":
        return PatternSet((Family(label or str(n), Pattern.from_int(n)),))

    def relabel(self, prefix: str) -> "PatternSet":
        return PatternSet(tuple(Family(f"{prefix}:{fam.label}", fam.pattern) for fam in self.families))

    def multiply(self, other: "PatternSet", label: str | None = None) -> "PatternSet":
        out = []
        for left in self.families:
            for right in other.families:
                fam_label = label or f"{left.label} * {right.label}"
                out.append(Family(fam_label, left.pattern.multiply(right.pattern)))
        return PatternSet(tuple(out))

    def union(self, *others: "PatternSet") -> "PatternSet":
        return PatternSet(self.families + tuple(itertools.chain.from_iterable(o.families for o in others)))

    def exclude_moduli(self, moduli: Iterable[int]) -> "PatternSet":
        families = list(self.families)
        for modulus in moduli:
            families = [Family(f.label, f.pattern.exclude_int(modulus)) for f in families]
        return PatternSet(tuple(families))

    def collisions(self) -> list[dict[str, str]]:
        out = []
        for i, left in enumerate(self.families):
            for right in self.families[i + 1:]:
                if left.pattern.overlaps(right.pattern):
                    out.append({
                        "left": left.label,
                        "left_pattern": left.pattern.render(),
                        "right": right.label,
                        "right_pattern": right.pattern.render(),
                    })
        return out

    def min_modulus(self) -> int | None:
        mins = [fam.pattern.min_modulus() for fam in self.families]
        if any(value is None for value in mins):
            return None
        return min(value for value in mins if value is not None)

    def summary(self) -> dict:
        collisions = self.collisions()
        return {
            "family_count": len(self.families),
            "min_symbolic_modulus": self.min_modulus(),
            "collision_count": len(collisions),
            "collisions": collisions,
            "families": [
                {"label": fam.label, "pattern": fam.pattern.render()}
                for fam in self.families
            ],
        }


EMPTY: PatternSet | None = None
X: PatternSet | None = None


def add(*sets: PatternSet | None) -> PatternSet:
    kept = [s for s in sets if s is not None]
    if not kept:
        return PatternSet(())
    return reduce(lambda left, right: left.union(right), kept)


def mul(*sets: PatternSet, label: str | None = None) -> PatternSet:
    if not sets:
        return PatternSet.one()
    return reduce(lambda left, right: left.multiply(right, label=label), sets)


def split(q: int, inputs: list[PatternSet | None], label: str | None = None) -> PatternSet:
    """Ordinary q-way split q(...): multiply filled inputs by exactly q."""
    out = []
    q_factor = PatternSet.integer(q)
    for index, nested in enumerate(inputs, start=1):
        if nested is None:
            continue
        branch = q_factor.multiply(nested)
        out.append(branch.relabel(f"{label or q}[{index}]"))
    return add(*out)


def arrow(q: int, inputs: list[PatternSet | None] | None = None, m: int = 1, label: str | None = None) -> PatternSet:
    """Arrow (q^m)^up(...): multiply filled inputs by q^a, a >= m."""
    if inputs is None:
        if q != 2:
            raise ValueError("only binary arrows default to one filled input")
        inputs = [PatternSet.one()]
    out = []
    q_family = PatternSet((Family(f"{q}^{m}up", Pattern.arrow_power(q, m)),))
    for index, nested in enumerate(inputs, start=1):
        if nested is None:
            continue
        branch = q_family.multiply(nested)
        out.append(branch.relabel(f"{label or str(q) + '^up'}[{index}]"))
    return add(*out)


def int_set(n: int) -> PatternSet:
    return PatternSet.integer(n)


@dataclass(frozen=True)
class Coverage:
    """Open-input bookkeeping for one symbolic expression."""

    open_paths: tuple[str, ...] = ()
    prefilled_paths: tuple[str, ...] = ()
    filled_paths: tuple[str, ...] = ()

    @staticmethod
    def filled(label: str = "filled") -> "Coverage":
        return Coverage(filled_paths=(label,))

    @staticmethod
    def prefilled(label: str = "x") -> "Coverage":
        return Coverage(prefilled_paths=(label,))

    @staticmethod
    def hole(label: str = "empty") -> "Coverage":
        return Coverage(open_paths=(label,))

    def relabel(self, prefix: str) -> "Coverage":
        def add_prefix(paths: tuple[str, ...]) -> tuple[str, ...]:
            return tuple(f"{prefix}/{path}" for path in paths)

        return Coverage(
            open_paths=add_prefix(self.open_paths),
            prefilled_paths=add_prefix(self.prefilled_paths),
            filled_paths=add_prefix(self.filled_paths),
        )

    def union(self, *others: "Coverage") -> "Coverage":
        return Coverage(
            open_paths=self.open_paths + tuple(itertools.chain.from_iterable(o.open_paths for o in others)),
            prefilled_paths=self.prefilled_paths + tuple(
                itertools.chain.from_iterable(o.prefilled_paths for o in others)
            ),
            filled_paths=self.filled_paths + tuple(itertools.chain.from_iterable(o.filled_paths for o in others)),
        )

    def summary(self) -> dict:
        return {
            "open_count": len(self.open_paths),
            "prefilled_x_count": len(self.prefilled_paths),
            "filled_count": len(self.filled_paths),
            "open_paths": list(self.open_paths),
            "prefilled_x_paths": list(self.prefilled_paths),
        }


COV_EMPTY: Coverage | None = None
COV_X = Coverage.prefilled()
COV_FILLED = Coverage.filled()


def cov_add(*coverages: Coverage | None) -> Coverage:
    kept = [coverage for coverage in coverages if coverage is not None]
    if not kept:
        return Coverage()
    return reduce(lambda left, right: left.union(right), kept)


def cov_split(q: int, inputs: list[Coverage | None], label: str | None = None) -> Coverage:
    """Coverage slots for ordinary q(...), where None is a genuine blank."""
    if len(inputs) != q:
        raise ValueError(f"ordinary split {q}(...) needs {q} inputs, got {len(inputs)}")
    out = []
    for index, nested in enumerate(inputs, start=1):
        path = f"{label or q}[{index}]"
        if nested is None:
            out.append(Coverage.hole(path))
        else:
            out.append(nested.relabel(path))
    return cov_add(*out)


def cov_arrow(q: int, inputs: list[Coverage | None], label: str | None = None) -> Coverage:
    """Coverage slots for q^up(...), with q-1 visible inputs."""
    if len(inputs) != q - 1:
        raise ValueError(f"arrow {q}^up(...) needs {q - 1} inputs, got {len(inputs)}")
    out = []
    for index, nested in enumerate(inputs, start=1):
        path = f"{label or str(q) + '^up'}[{index}]"
        if nested is None:
            out.append(Coverage.hole(path))
        else:
            out.append(nested.relabel(path))
    return cov_add(*out)


def paper_sample() -> PatternSet:
    """Nielsen's explanatory sample: 5^up(1, 2, 4, 3^up(1, 2^up))."""
    return arrow(5, [
        int_set(1),
        int_set(2),
        int_set(4),
        arrow(3, [int_set(1), arrow(2)]),
    ], label="sample_5up")


def section4_initial() -> PatternSet:
    """Modulus-family bookkeeping for the first construction moves."""
    s41 = arrow(2, label="4.1 2up").exclude_moduli([2, 4, 8, 16, 32])

    s42_main = arrow(3, [int_set(2), arrow(2, m=2, label="4up")], label="4.2 3up").exclude_moduli(
        [6, 12, 18, 24, 36]
    )
    s42_extra = mul(PatternSet.integer(27), arrow(3, [int_set(1), EMPTY], label="4.2 extra 81up"))

    s43_main = split(5, [
        int_set(8),
        arrow(2, m=4, label="16up"),
        split(3, [
            int_set(4),
            arrow(3, [int_set(4), EMPTY], label="9up_partial"),
            arrow(3, [int_set(1), int_set(2)], label="9up_full"),
        ], label="3_split"),
        arrow(3, [int_set(8), arrow(2, m=4, label="16up")], label="3up_8_16up"),
        arrow(5, [
            int_set(2),
            arrow(2, m=2, label="4up"),
            arrow(3, [int_set(1), int_set(2)], label="3up_1_2"),
            arrow(3, [int_set(4), arrow(2, m=3, label="8up")], label="3up_4_8up"),
        ], m=2, label="25up"),
    ], label="4.3 5")
    s43_extra = arrow(5, [int_set(1), EMPTY, EMPTY, EMPTY], m=3, label="4.3 extra 125up")

    return add(s41, s42_main, s42_extra, s43_main, s43_extra)


def set_a_4_4() -> list[PatternSet]:
    """The ordered set A from Subsection 4.4."""
    return [
        int_set(2),
        int_set(4),
        arrow(3, [int_set(1), int_set(2)], label="A:3up_1_2"),
        int_set(1),
        arrow(2, m=3, label="A:8up"),
        arrow(3, [int_set(4), arrow(2, m=3, label="A:8up")], label="A:3up_4_8up"),
    ]


def section4_4() -> PatternSet:
    """Modulus-family bookkeeping for Subsection 4.4, the prime 7."""
    eight_up = arrow(2, m=3, label="8up")
    three_up_1_2 = arrow(3, [int_set(1), int_set(2)], label="3up_1_2")
    three_up_4_8up = arrow(3, [int_set(4), eight_up], label="3up_4_8up")
    nine_up_1_2 = arrow(3, [int_set(1), int_set(2)], m=2, label="9up_1_2")
    nine_up_4_8up = arrow(3, [int_set(4), eight_up], m=2, label="9up_4_8up")

    s44_main = split(7, [
        EMPTY,
        eight_up,
        split(3, [int_set(2), int_set(4), three_up_1_2], label="4.4 branch3"),
        split(5, [
            arrow(5, [int_set(1), int_set(2), int_set(4), eight_up], label="5up_1_2_4_8up"),
            int_set(2),
            split(3, [int_set(1), int_set(2), X], label="3_split_x"),
            int_set(4),
            split(5, [X, X, X, three_up_1_2, X], label="5_split_x_3up_1_2"),
        ], label="4.4 branch4"),
        add(
            split(3, [eight_up, three_up_4_8up, EMPTY], label="4.4 branch5 left"),
            split(5, [
                mul(int_set(3), int_set(4), label="3*4"),
                nine_up_1_2,
                X,
                nine_up_4_8up,
                split(5, [
                    X,
                    X,
                    X,
                    arrow(5, [
                        mul(int_set(3), int_set(1), label="3*1"),
                        mul(int_set(3), int_set(2), label="3*2"),
                        mul(int_set(3), int_set(4), label="3*4"),
                        mul(int_set(3), eight_up, label="3*8up"),
                    ], label="5up_3_times"),
                    X,
                ], label="5_split_x_5up"),
            ], label="4.4 branch5 right"),
        ),
        split(5, [
            eight_up,
            EMPTY,
            split(3, [eight_up, EMPTY, X], label="3_split_8up_x"),
            EMPTY,
            split(5, [X, X, X, three_up_4_8up, X], label="5_split_x_3up_4_8up"),
        ], label="4.4 branch6"),
        EMPTY,
    ], label="4.4 7")

    a = set_a_4_4()
    s44_right_white = arrow(7, a, m=2, label="4.4 right white 49up")
    s44_gray_mod5 = mul(int_set(5), arrow(7, a, m=2, label="4.4 gray 49up"))
    s44_left_mod25 = mul(int_set(25), arrow(7, a, m=2, label="4.4 left 49up"))

    return add(s44_main, s44_right_white, s44_gray_mod5, s44_left_mod25)


def section4_through_4_4() -> PatternSet:
    return add(section4_initial(), section4_4())


# ---- Subsection 4.5: prime 11, fills holes from moduli 6 and 18 (1 mod 4 half) ----

def _section4_5_inputs(*, x_for_4_or_8up: bool = False,
                       swap_4_to_1_and_8up_to_2: bool = False) -> list[PatternSet | None]:
    """Build the 10 inputs of Subsection 4.5's 11^up.

    Pure modulus-family bookkeeping.  Two flags reflect Subsection 4.6's
    modifications when reusing this structure inside the 13^up's last two
    inputs:

      x_for_4_or_8up:           replace each `4` or `8^up` leaf by `x`
                                (it was covered in the previous subsection).
      swap_4_to_1_and_8up_to_2: replace each `4` by `1` and each `8^up` by `2`.

    The flags are mutually exclusive in spirit.  Setting both means: first
    swap, then x-out the entries that remain `1` or `2` — but Nielsen's 4.6
    last input applies them sequentially with `x` first, then swap, so it's
    cleanest to call this twice with different flags.
    """
    if x_for_4_or_8up and swap_4_to_1_and_8up_to_2:
        raise ValueError("flags should be set one at a time, not together")

    def four_leaf() -> PatternSet | None:
        if x_for_4_or_8up:
            return X
        if swap_4_to_1_and_8up_to_2:
            return int_set(1)
        return int_set(4)

    def eight_up_leaf() -> PatternSet | None:
        if x_for_4_or_8up:
            return X
        if swap_4_to_1_and_8up_to_2:
            return int_set(2)
        return arrow(2, m=3, label="8up")

    eight_up = arrow(2, m=3, label="8up")
    nine = int_set(9)
    twenty_seven = int_set(27)

    # 27^up · v  = arrow(3, [v, EMPTY], m=3)
    def twenty_seven_up_one(value: PatternSet, label: str) -> PatternSet:
        return arrow(3, [value, EMPTY], m=3, label=label)

    eighty_one_up_1_4 = arrow(3, [int_set(1), int_set(4)], m=4, label="81up_1_4")

    common3 = add(
        mul(int_set(3), int_set(2), label="3*2"),
        mul(twenty_seven, int_set(1), label="27*1"),
        twenty_seven_up_one(int_set(2), label="27up*2"),
    )
    common4 = add(
        mul(int_set(3), four_leaf(), label="3*4_leaf") if four_leaf() is not None else PatternSet(()),
        mul(twenty_seven, four_leaf(), label="27*4_leaf") if four_leaf() is not None else PatternSet(()),
        twenty_seven_up_one(eight_up_leaf(), label="27up*8up_leaf") if eight_up_leaf() is not None else PatternSet(()),
    )
    common8 = add(
        mul(int_set(3), split(3, [int_set(1), int_set(2), four_leaf()], label="3_1_2_4_leaf"),
            label="3*3(1,2,4_leaf)"),
        eighty_one_up_1_4,
        arrow(5, [
            twenty_seven_up_one(int_set(1), label="27up*1"),
            twenty_seven_up_one(int_set(2), label="27up*2"),
            twenty_seven_up_one(four_leaf(), label="27up*4_leaf") if four_leaf() is not None else None,
            twenty_seven_up_one(eight_up_leaf(), label="27up*8up_leaf") if eight_up_leaf() is not None else None,
        ], label="5up_27up_quads"),
    )

    input5 = add(
        mul(int_set(3), eight_up_leaf(), label="3*8up_leaf") if eight_up_leaf() is not None else PatternSet(()),
        mul(nine, eight_up_leaf(), label="9*8up_leaf") if eight_up_leaf() is not None else PatternSet(()),
    )

    input6 = arrow(5, [
        int_set(1),
        int_set(2),
        mul(int_set(3), int_set(1), label="3*1"),
        four_leaf(),
    ], label="5up_1_2_3*1_4leaf")

    input7 = arrow(5, [
        eight_up_leaf(),
        add(mul(int_set(3), int_set(2), label="3*2"),
            mul(nine, int_set(2), label="9*2")),
        mul(int_set(3), four_leaf(), label="3*4_leaf") if four_leaf() is not None else None,
        add(
            mul(int_set(3), eight_up_leaf(), label="3*8up_leaf") if eight_up_leaf() is not None else PatternSet(()),
            mul(nine, eight_up_leaf(), label="9*8up_leaf") if eight_up_leaf() is not None else PatternSet(()),
        ),
    ], label="5up_input7")

    input9 = arrow(7, [
        int_set(1),
        int_set(2),
        mul(int_set(3), int_set(1), label="3*1"),
        arrow(5, [int_set(1), int_set(2), X, four_leaf()], label="5up_1_2_x_4leaf"),
        four_leaf(),
        eight_up_leaf(),
    ], label="7up_input9")

    input10_first = arrow(5, [
        split(3, [
            split(3, [int_set(1), four_leaf(), EMPTY], label="3(1,4leaf,_)"),
            EMPTY, EMPTY,
        ], label="3(3(1,4leaf,_),_,_)"),
        EMPTY, EMPTY, EMPTY,
    ], label="5up_input10_first")

    inner5up_4 = arrow(5, [
        add(
            mul(int_set(3), split(3, [X, X, int_set(1)], label="3(x,x,1)"), label="3*3(x,x,1)"),
            mul(nine, int_set(2), label="9*2"),
        ),
        eight_up_leaf(),
        X,
        add(mul(int_set(3), int_set(1), label="3*1"),
            mul(nine, four_leaf(), label="9*4_leaf") if four_leaf() is not None else PatternSet(())),
    ], label="5up_input10_inner4")

    inner5up_6 = arrow(5, [
        mul(int_set(3), split(3, [X, X, eight_up_leaf()], label="3(x,x,8up_leaf)"),
            label="3*3(x,x,8up_leaf)"),
        mul(int_set(3), int_set(2), label="3*2"),
        mul(int_set(3), four_leaf(), label="3*4_leaf") if four_leaf() is not None else None,
        mul(int_set(3), eight_up_leaf(), label="3*8up_leaf") if eight_up_leaf() is not None else None,
    ], label="5up_input10_inner6_left")

    input10_second = arrow(7, [
        common3,
        common4,
        mul(int_set(3), eight_up_leaf(), label="3*8up_leaf") if eight_up_leaf() is not None else None,
        inner5up_4,
        common8,
        add(inner5up_6,
            mul(nine, eight_up_leaf(), label="9*8up_leaf") if eight_up_leaf() is not None else PatternSet(())),
    ], label="7up_input10")

    input10 = add(input10_first, input10_second)

    return [
        four_leaf(),       # 1
        eight_up_leaf(),   # 2
        common3,           # 3
        common4,           # 4
        input5,            # 5
        input6,            # 6
        input7,            # 7
        common8,           # 8
        input9,            # 9
        input10,           # 10
    ]


def section4_5() -> PatternSet:
    """Modulus-family bookkeeping for Subsection 4.5, the prime 11.

    The 11^up has 10 inputs.  All are filled (no new holes per Nielsen).

    The sub-expressions

        common3 = 3 · 2 + 27 · 1 + 27^up · 2,
        common4 = 3 · 4 + 27 · 4 + 27^up · 8^up,
        common8 = 3 · 3(1,2,4) + 81^up(1,4)
                  + 5^up(27^up · 1, 27^up · 2, 27^up · 4, 27^up · 8^up)

    are reused as inputs 3, 4, 8 of the outer 11^up and also as inputs 1, 2, 5
    of the inner 7^up inside the tenth 11^up input.
    """
    return arrow(11, _section4_5_inputs(), label="4.5 11up")


def _legacy_section4_5() -> PatternSet:
    """Original inline encoding of 4.5, kept for cross-checking against
    `section4_5()` which is now built from `_section4_5_inputs`."""
    eight_up = arrow(2, m=3, label="8up")
    nine = int_set(9)
    twenty_seven = int_set(27)

    three_up_1_2 = arrow(3, [int_set(1), int_set(2)], label="3up_1_2")

    # 27^up · v  = arrow(3, [v, EMPTY], m=3): prime-3 arrow with floor 3, one filled input.
    def twenty_seven_up_one(value: PatternSet, label: str) -> PatternSet:
        return arrow(3, [value, EMPTY], m=3, label=label)

    # 81^up(a, b) = arrow(3, [a, b], m=4)
    eighty_one_up_1_4 = arrow(3, [int_set(1), int_set(4)], m=4, label="81up_1_4")

    common3 = add(
        mul(int_set(3), int_set(2), label="3*2"),
        mul(twenty_seven, int_set(1), label="27*1"),
        twenty_seven_up_one(int_set(2), label="27up*2"),
    )
    common4 = add(
        mul(int_set(3), int_set(4), label="3*4"),
        mul(twenty_seven, int_set(4), label="27*4"),
        twenty_seven_up_one(eight_up, label="27up*8up"),
    )
    common8 = add(
        mul(int_set(3), split(3, [int_set(1), int_set(2), int_set(4)], label="3_1_2_4"),
            label="3*3(1,2,4)"),
        eighty_one_up_1_4,
        arrow(5, [
            twenty_seven_up_one(int_set(1), label="27up*1"),
            twenty_seven_up_one(int_set(2), label="27up*2"),
            twenty_seven_up_one(int_set(4), label="27up*4"),
            twenty_seven_up_one(eight_up, label="27up*8up"),
        ], label="5up_27up_quads"),
    )

    # Input 5: 3 · 8^up + 9 · 8^up
    input5 = add(
        mul(int_set(3), eight_up, label="3*8up"),
        mul(nine, eight_up, label="9*8up"),
    )

    # Input 6: 5^up(1, 2, 3·1, 4)
    input6 = arrow(5, [
        int_set(1),
        int_set(2),
        mul(int_set(3), int_set(1), label="3*1"),
        int_set(4),
    ], label="5up_1_2_3*1_4")

    # Input 7: 5^up(8^up, 3·2 + 9·2, 3·4, 3·8^up + 9·8^up)
    input7 = arrow(5, [
        eight_up,
        add(
            mul(int_set(3), int_set(2), label="3*2"),
            mul(nine, int_set(2), label="9*2"),
        ),
        mul(int_set(3), int_set(4), label="3*4"),
        add(
            mul(int_set(3), eight_up, label="3*8up"),
            mul(nine, eight_up, label="9*8up"),
        ),
    ], label="5up_8up_3*2+9*2_3*4_3*8up+9*8up")

    # Input 9: 7^up(1, 2, 3·1, 5^up(1, 2, x, 4), 4, 8^up)
    input9 = arrow(7, [
        int_set(1),
        int_set(2),
        mul(int_set(3), int_set(1), label="3*1"),
        arrow(5, [int_set(1), int_set(2), X, int_set(4)], label="5up_1_2_x_4"),
        int_set(4),
        eight_up,
    ], label="7up_input9")

    # Input 10 first part: 5^up(3(3(1, 4, EMPTY), EMPTY, EMPTY), EMPTY, EMPTY, EMPTY)
    input10_first = arrow(5, [
        split(3, [
            split(3, [int_set(1), int_set(4), EMPTY], label="3(1,4,_)"),
            EMPTY,
            EMPTY,
        ], label="3(3(1,4,_),_,_)"),
        EMPTY,
        EMPTY,
        EMPTY,
    ], label="5up_input10_first")

    # Input 10 second part: 7^up( common3, common4, 3·8^up,
    #     5^up(3·3(x,x,1) + 9·2, 8^up, x, 3·1 + 9·4),
    #     common8,
    #     5^up(3·3(x,x,8^up), 3·2, 3·4, 3·8^up) + 9·8^up )
    inner5up_4 = arrow(5, [
        add(
            mul(int_set(3), split(3, [X, X, int_set(1)], label="3(x,x,1)"),
                label="3*3(x,x,1)"),
            mul(nine, int_set(2), label="9*2"),
        ),
        eight_up,
        X,
        add(
            mul(int_set(3), int_set(1), label="3*1"),
            mul(nine, int_set(4), label="9*4"),
        ),
    ], label="5up_input10_inner4")

    inner5up_6 = arrow(5, [
        mul(int_set(3), split(3, [X, X, eight_up], label="3(x,x,8up)"),
            label="3*3(x,x,8up)"),
        mul(int_set(3), int_set(2), label="3*2"),
        mul(int_set(3), int_set(4), label="3*4"),
        mul(int_set(3), eight_up, label="3*8up"),
    ], label="5up_input10_inner6_left")

    input10_second = arrow(7, [
        common3,
        common4,
        mul(int_set(3), eight_up, label="3*8up"),
        inner5up_4,
        common8,
        add(inner5up_6, mul(nine, eight_up, label="9*8up")),
    ], label="7up_input10")

    input10 = add(input10_first, input10_second)

    s45_main = arrow(11, [
        int_set(4),                                # 1
        eight_up,                                  # 2
        common3,                                   # 3
        common4,                                   # 4
        input5,                                    # 5
        input6,                                    # 6
        input7,                                    # 7
        common8,                                   # 8
        input9,                                    # 9
        input10,                                   # 10
    ], label="4.5 11up")

    return s45_main


def section4_through_4_5() -> PatternSet:
    return add(section4_initial(), section4_4(), section4_5())


# ---- Subsection 4.6: prime 13, 3 mod 4 half (parallel to 4.5) ----

def section4_6() -> PatternSet:
    """Modulus-family bookkeeping for Subsection 4.6, the prime 13.

    The 13^up has 12 inputs.  Per Nielsen:

    - Inputs 1..10 reuse the same modulus-family structure as the 10 inputs of
      Subsection 4.5's 11^up.  (The residues are on the `3 mod 4` branch
      rather than `1 mod 4`, but residues do not affect modulus families.)
    - Input 11 is a modified 11^up: same inputs as Subsection 4.5's 11^up, but
      with each `4` and `8^up` replaced by `x` (they were already covered in
      Subsection 4.5).  Modulus-wise, an `x` is *prefilled* and contributes
      no new family.
    - Input 12 is another 11^up: again `4` and `8^up` are `x`-ed, then every
      remaining `4` is swapped to `1` and every `8^up` to `2`.  Because the
      first swap is to `x`, the swap-step here only takes effect on positions
      where `4`/`8^up` did not appear as leaves — which in our encoding means
      nothing further changes for the modulus families.

    For collision-checking purposes, only the difference between inputs 11 and
    12 that matters is which leaves are present.  Both have the same structural
    skeleton, lifted by 13^up · 11^up.
    """
    # Inputs 1..10: exactly the 4.5 inputs, but lifted by 13^up instead of 11^up.
    inputs_1_to_10 = _section4_5_inputs()

    # Input 11: 11^up with the 4.5 inputs, all `4` and `8^up` leaves replaced by `x`.
    input_11_inner = _section4_5_inputs(x_for_4_or_8up=True)
    input_11 = arrow(11, input_11_inner, label="4.6 input11 11up")

    # Input 12: 11^up with the 4.5 inputs, `4` → `1` and `8^up` → `2`.
    input_12_inner = _section4_5_inputs(swap_4_to_1_and_8up_to_2=True)
    input_12 = arrow(11, input_12_inner, label="4.6 input12 11up")

    s46_main = arrow(13, inputs_1_to_10 + [input_11, input_12], label="4.6 13up")
    return s46_main


def section4_through_4_6() -> PatternSet:
    return add(section4_initial(), section4_4(), section4_5(), section4_6())


def section4_6_coverage() -> dict:
    """Coverage-slot summary for Subsection 4.6.

    Per the paper, all 12 inputs of 13^up are filled (no new holes).  Inputs
    1..10 mirror 4.5's 10 inputs.  Inputs 11 and 12 are modified 11^up's, with
    `x` markers on entries that were covered in 4.5.
    """
    def filled_11up_with_x_swap() -> Coverage:
        # Same skeleton as 4.5's 11^up coverage but with the `4` and `8^up`
        # leaves treated as prefilled `x` rather than filled.
        return cov_arrow(11, [
            COV_X,         # 1: 4 → x
            COV_X,         # 2: 8^up → x
            COV_FILLED,    # 3: common3
            COV_FILLED,    # 4: common4
            COV_FILLED,    # 5: 3·8^up + 9·8^up  (8^up children become x but the family is still filled)
            cov_arrow(5, [COV_FILLED, COV_FILLED, COV_FILLED, COV_X], label="6: 5up"),
            cov_arrow(5, [COV_X, COV_FILLED, COV_FILLED, COV_FILLED], label="7: 5up"),
            COV_FILLED,    # 8: common8
            cov_arrow(7, [
                COV_FILLED, COV_FILLED, COV_FILLED,
                cov_arrow(5, [COV_FILLED, COV_FILLED, COV_X, COV_X], label="9/5up"),
                COV_X, COV_X,
            ], label="9: 7up"),
            cov_add(
                cov_arrow(5, [
                    cov_split(3, [
                        cov_split(3, [COV_FILLED, COV_X, COV_EMPTY], label="10a/3a"),
                        COV_EMPTY, COV_EMPTY,
                    ], label="10a/3"),
                    COV_EMPTY, COV_EMPTY, COV_EMPTY,
                ], label="10a: 5up_first"),
                cov_arrow(7, [
                    COV_FILLED, COV_FILLED, COV_FILLED,
                    cov_arrow(5, [COV_FILLED, COV_X, COV_X, COV_FILLED], label="10b/4_5up"),
                    COV_FILLED, COV_FILLED,
                ], label="10b: 7up"),
            ),
        ], label="modified 11up")

    raw_expression = cov_arrow(13, [
        COV_FILLED,   # 1: 4 (now refers to 3 mod 4 branch)
        COV_FILLED,   # 2: 8^up
        COV_FILLED,   # 3: common3
        COV_FILLED,   # 4: common4
        COV_FILLED,   # 5
        cov_arrow(5, [COV_FILLED, COV_FILLED, COV_FILLED, COV_FILLED], label="6: 5up"),
        cov_arrow(5, [COV_FILLED, COV_FILLED, COV_FILLED, COV_FILLED], label="7: 5up"),
        COV_FILLED,   # 8: common8
        cov_arrow(7, [
            COV_FILLED, COV_FILLED, COV_FILLED,
            cov_arrow(5, [COV_FILLED, COV_FILLED, COV_X, COV_FILLED], label="9/5up"),
            COV_FILLED, COV_FILLED,
        ], label="9: 7up"),
        cov_add(
            cov_arrow(5, [
                cov_split(3, [
                    cov_split(3, [COV_FILLED, COV_FILLED, COV_EMPTY], label="10a/3a"),
                    COV_EMPTY, COV_EMPTY,
                ], label="10a/3"),
                COV_EMPTY, COV_EMPTY, COV_EMPTY,
            ], label="10a: 5up_first"),
            cov_arrow(7, [
                COV_FILLED, COV_FILLED, COV_FILLED,
                cov_arrow(5, [COV_FILLED, COV_FILLED, COV_X, COV_FILLED], label="10b/4_5up"),
                COV_FILLED, COV_FILLED,
            ], label="10b: 7up"),
        ),
        filled_11up_with_x_swap().relabel("11: modified 11up (x for 4,8up)"),
        filled_11up_with_x_swap().relabel("12: modified 11up (x then 4->1, 8up->2)"),
    ], label="4.6 raw 13up")

    final_residual = Coverage()  # Per paper: no new holes.

    return {
        "raw_expression": raw_expression.summary(),
        "final_residual_from_text": final_residual.summary(),
        "notes": [
            "13^up has 12 inputs; inputs 1..10 mirror 4.5's 11^up (residues only differ).",
            "Inputs 11 and 12 are modified 11^up's: in 11, replace each 4 and 8^up by x.",
            "In 12, also swap each remaining 4 to 1 and each 8^up to 2.",
            "Paper states no new holes are created by Subsection 4.6.",
        ],
    }


def section4_5_coverage() -> dict:
    """Coverage-slot summary for Subsection 4.5.

    Nielsen states explicitly: 4.5 fills holes from moduli 6 and 18 on the
    1 (mod 4) half "without creating any new holes".  All ten inputs of 11^up
    are intended to be fully covered.  The two raw structural blanks below
    (input 10's first 5^up has 3 inert blanks) are filled by the within-input
    sum with the parallel 7^up.
    """
    # Raw 11^up has all 10 inputs filled.
    raw_expression = cov_arrow(11, [
        COV_FILLED,   # 1: 4
        COV_FILLED,   # 2: 8^up
        COV_FILLED,   # 3: common3
        COV_FILLED,   # 4: common4
        COV_FILLED,   # 5: 3·8^up + 9·8^up
        cov_arrow(5, [COV_FILLED, COV_FILLED, COV_FILLED, COV_FILLED], label="6: 5up"),
        cov_arrow(5, [COV_FILLED, COV_FILLED, COV_FILLED, COV_FILLED], label="7: 5up"),
        COV_FILLED,   # 8: common8
        cov_arrow(7, [
            COV_FILLED, COV_FILLED, COV_FILLED,
            cov_arrow(5, [COV_FILLED, COV_FILLED, COV_X, COV_FILLED], label="9/5up"),
            COV_FILLED, COV_FILLED,
        ], label="9: 7up"),
        cov_add(
            # Input 10 first: 5^up with 3 raw blanks filled by the parallel 7^up
            cov_arrow(5, [
                cov_split(3, [
                    cov_split(3, [COV_FILLED, COV_FILLED, COV_EMPTY], label="10a/3a"),
                    COV_EMPTY,
                    COV_EMPTY,
                ], label="10a/3"),
                COV_EMPTY,
                COV_EMPTY,
                COV_EMPTY,
            ], label="10a: 5up_first"),
            # Input 10 second: 7^up with all 6 inputs filled
            cov_arrow(7, [
                COV_FILLED,
                COV_FILLED,
                COV_FILLED,
                cov_arrow(5, [
                    COV_FILLED, COV_FILLED, COV_X, COV_FILLED
                ], label="10b/4_5up"),
                COV_FILLED,
                COV_FILLED,
            ], label="10b: 7up"),
        ),
    ], label="4.5 raw 11up")

    final_residual = Coverage()  # Per paper: no new holes created.

    return {
        "raw_expression": raw_expression.summary(),
        "final_residual_from_text": final_residual.summary(),
        "notes": [
            "11^up has 10 inputs, all 10 are filled.",
            "Input 10 first half (5^up(3(3(1,4,_),_,_),_,_,_)) has raw blanks; "
            "these are intended to be filled by the within-input sum with the parallel 7^up.",
            "Paper states no new holes are created by Subsection 4.5.",
        ],
    }


def section4_4_coverage() -> dict:
    """Coverage-slot summary for Subsection 4.4.

    This intentionally does not try to prove the residue-level claims.  It
    records the syntactic distinction needed for the next checker layer: blanks
    are open work, while `x` slots are already filled by earlier subsections.
    """
    raw_expression = cov_split(7, [
        COV_EMPTY,
        COV_FILLED,
        cov_split(3, [COV_FILLED, COV_FILLED, cov_arrow(3, [COV_FILLED, COV_FILLED], label="3up")],
                  label="branch3"),
        cov_split(5, [
            cov_arrow(5, [COV_FILLED, COV_FILLED, COV_FILLED, COV_FILLED], label="5up"),
            COV_FILLED,
            cov_split(3, [COV_FILLED, COV_FILLED, COV_X], label="branch4/3"),
            COV_FILLED,
            cov_split(5, [COV_X, COV_X, COV_X, COV_FILLED, COV_X], label="branch4/5"),
        ], label="branch4"),
        cov_add(
            cov_split(3, [COV_FILLED, COV_FILLED, COV_EMPTY], label="branch5/3"),
            cov_split(5, [
                COV_FILLED,
                COV_FILLED,
                COV_X,
                COV_FILLED,
                cov_split(5, [COV_X, COV_X, COV_X, COV_FILLED, COV_X], label="branch5/5/5"),
            ], label="branch5/5"),
        ),
        cov_split(5, [
            COV_FILLED,
            COV_EMPTY,
            cov_split(3, [COV_FILLED, COV_EMPTY, COV_X], label="branch6/3"),
            COV_EMPTY,
            cov_split(5, [COV_X, COV_X, COV_X, COV_FILLED, COV_X], label="branch6/5"),
        ], label="branch6"),
        COV_EMPTY,
    ], label="4.4 raw 7")

    final_residual = Coverage(
        open_paths=(
            "4.4 final/left hole: empty except class 20 mod 25 is filled",
            "4.4 final/right gray hole: one class mod 5 remains",
            "4.4 final/right gray hole: one class mod 5*3 remains",
        )
    )

    return {
        "raw_expression": raw_expression.summary(),
        "final_residual_from_text": final_residual.summary(),
        "notes": [
            "`x` entries are counted as prefilled slots, not as new modulus families.",
            "The final residual holes are Nielsen's prose summary after the 49^up fillers.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--example",
        choices=[
            "paper_sample",
            "section4_initial",
            "section4_4",
            "section4_through_4_4",
            "section4_4_coverage",
            "section4_5",
            "section4_through_4_5",
            "section4_5_coverage",
            "section4_6",
            "section4_through_4_6",
            "section4_6_coverage",
        ],
        default="paper_sample",
    )
    args = parser.parse_args()

    if args.example == "paper_sample":
        result = {"example": args.example, **paper_sample().summary()}
    elif args.example == "section4_initial":
        result = {"example": args.example, **section4_initial().summary()}
    elif args.example == "section4_4":
        result = {"example": args.example, **section4_4().summary()}
    elif args.example == "section4_through_4_4":
        result = {"example": args.example, **section4_through_4_4().summary()}
    elif args.example == "section4_4_coverage":
        result = {"example": args.example, **section4_4_coverage()}
    elif args.example == "section4_5":
        result = {"example": args.example, **section4_5().summary()}
    elif args.example == "section4_through_4_5":
        result = {"example": args.example, **section4_through_4_5().summary()}
    elif args.example == "section4_5_coverage":
        result = {"example": args.example, **section4_5_coverage()}
    elif args.example == "section4_6":
        result = {"example": args.example, **section4_6().summary()}
    elif args.example == "section4_through_4_6":
        result = {"example": args.example, **section4_through_4_6().summary()}
    else:
        result = {"example": args.example, **section4_6_coverage()}
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
