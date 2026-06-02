"""
Verify finite covering systems of congruences.

A covering system is a finite list of congruences

    n == residue (mod modulus)

whose union covers every integer.  For a finite system this can be checked on
one period, normally the lcm of the moduli.  For large recursive constructions
where a known period is supplied, this script verifies coverage modulo that
period in memory-bounded chunks.

Input JSON format:

{
  "name": "example",
  "period": 12,
  "congruences": [
    {"residue": 0, "modulus": 2},
    {"residue": 0, "modulus": 3}
  ]
}

Usage:
  python3 erdos_covering/verify_covering.py erdos_covering/examples/erdos_5.json
  python3 erdos_covering/verify_covering.py system.json --period 223092870
"""
from __future__ import annotations

import argparse
import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


@dataclass(frozen=True)
class Congruence:
    residue: int
    modulus: int

    def normalized(self) -> "Congruence":
        if self.modulus <= 1:
            raise ValueError(f"modulus must be > 1, got {self.modulus}")
        return Congruence(self.residue % self.modulus, self.modulus)


def lcm(a: int, b: int) -> int:
    return a // math.gcd(a, b) * b


def parse_congruence(row: object) -> Congruence:
    if isinstance(row, dict):
        if "residue" in row:
            residue = row["residue"]
        else:
            residue = row.get("a")
        if "modulus" in row:
            modulus = row["modulus"]
        else:
            modulus = row.get("m")
        if residue is None or modulus is None:
            raise ValueError(f"missing residue/modulus in {row!r}")
        return Congruence(int(residue), int(modulus)).normalized()
    if isinstance(row, (list, tuple)) and len(row) == 2:
        return Congruence(int(row[0]), int(row[1])).normalized()
    raise ValueError(f"cannot parse congruence {row!r}")


def load_system(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as fh:
        data = json.load(fh)
    raw = data.get("congruences", data if isinstance(data, list) else None)
    if raw is None:
        raise ValueError("JSON must be a list or contain a 'congruences' field")
    congruences = [parse_congruence(row) for row in raw]
    return {
        "name": data.get("name", path.stem) if isinstance(data, dict) else path.stem,
        "period": data.get("period") if isinstance(data, dict) else None,
        "congruences": congruences,
        "source": data.get("source") if isinstance(data, dict) else None,
    }


def validate_system(congruences: list[Congruence], require_distinct: bool = True) -> dict:
    if not congruences:
        raise ValueError("system must contain at least one congruence")
    moduli = [c.modulus for c in congruences]
    duplicate_moduli = sorted({m for m in moduli if moduli.count(m) > 1})
    duplicate_pairs = sorted({
        (c.residue, c.modulus)
        for c in congruences
        if congruences.count(c) > 1
    })
    if require_distinct and duplicate_moduli:
        raise ValueError(f"moduli are not distinct: {duplicate_moduli[:20]}")
    return {
        "count": len(congruences),
        "min_modulus": min(moduli),
        "max_modulus": max(moduli),
        "distinct_moduli": len(set(moduli)) == len(moduli),
        "duplicate_moduli": duplicate_moduli,
        "duplicate_pairs": duplicate_pairs,
    }


def lcm_period(congruences: Iterable[Congruence], max_lcm: int) -> int:
    period = 1
    for c in congruences:
        period = lcm(period, c.modulus)
        if period > max_lcm:
            raise ValueError(
                f"lcm period exceeded --max-lcm={max_lcm}; pass --period explicitly "
                "for a known construction period"
            )
    return period


def check_period_compatibility(congruences: Iterable[Congruence], period: int) -> list[int]:
    bad = [c.modulus for c in congruences if period % c.modulus != 0]
    return sorted(set(bad))


def mark_chunk(covered: bytearray, lo: int, hi: int, congruences: list[Congruence]) -> None:
    size = hi - lo
    for c in congruences:
        start = lo + ((c.residue - lo) % c.modulus)
        if start >= hi:
            continue
        offset = start - lo
        count = ((size - 1 - offset) // c.modulus) + 1
        covered[offset:size:c.modulus] = b"\x01" * count


def first_uncovered_in_chunk(covered: bytearray, lo: int) -> int | None:
    try:
        idx = covered.index(0)
    except ValueError:
        return None
    return lo + idx


def verify_coverage(
    congruences: list[Congruence],
    period: int,
    chunk_size: int,
    sample_uncovered: int = 10,
) -> dict:
    uncovered = []
    covered_count = 0
    for lo in range(0, period, chunk_size):
        hi = min(period, lo + chunk_size)
        covered = bytearray(hi - lo)
        mark_chunk(covered, lo, hi, congruences)
        chunk_covered = sum(covered)
        covered_count += chunk_covered
        if chunk_covered != hi - lo:
            idx = first_uncovered_in_chunk(covered, lo)
            while idx is not None and len(uncovered) < sample_uncovered:
                uncovered.append(idx)
                covered[idx - lo] = 1
                idx = first_uncovered_in_chunk(covered, lo)
            if len(uncovered) >= sample_uncovered:
                break
    return {
        "period": period,
        "covered": covered_count,
        "covered_fraction": covered_count / period if period else 0.0,
        "is_covering": not uncovered and covered_count == period,
        "uncovered_sample": uncovered,
    }


def residue_cover_counts(congruences: list[Congruence], period: int, chunk_size: int) -> dict:
    """Return overlap statistics for modest periods."""
    counts = {}
    for lo in range(0, period, chunk_size):
        hi = min(period, lo + chunk_size)
        local = bytearray(hi - lo)
        for c in congruences:
            start = lo + ((c.residue - lo) % c.modulus)
            if start >= hi:
                continue
            for x in range(start, hi, c.modulus):
                local[x - lo] = min(255, local[x - lo] + 1)
        for value in local:
            counts[int(value)] = counts.get(int(value), 0) + 1
    return {str(k): counts[k] for k in sorted(counts)}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("system", type=Path)
    parser.add_argument("--period", type=int, default=None,
                        help="known verification period; every modulus must divide it")
    parser.add_argument("--max-lcm", type=int, default=10_000_000,
                        help="maximum lcm to compute automatically")
    parser.add_argument("--chunk-size", type=int, default=2_000_000)
    parser.add_argument("--allow-repeated-moduli", action="store_true")
    parser.add_argument("--overlap-stats", action="store_true",
                        help="also compute coverage multiplicities; for small periods")
    args = parser.parse_args()

    system = load_system(args.system)
    congruences = system["congruences"]
    metadata = validate_system(congruences, require_distinct=not args.allow_repeated_moduli)

    period = args.period or system["period"]
    period_source = "provided"
    if period is None:
        period = lcm_period(congruences, args.max_lcm)
        period_source = "lcm"
    period = int(period)

    incompatible = check_period_compatibility(congruences, period)
    if incompatible:
        raise ValueError(
            f"period {period} is not divisible by these moduli: {incompatible[:20]}"
        )

    coverage = verify_coverage(congruences, period, args.chunk_size)
    result = {
        "name": system["name"],
        "source": system["source"],
        "system": metadata,
        "period_source": period_source,
        "coverage": coverage,
    }
    if args.overlap_stats:
        result["overlap_counts"] = residue_cover_counts(congruences, period, args.chunk_size)
    print(json.dumps(result, indent=2))
    return 0 if coverage["is_covering"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
