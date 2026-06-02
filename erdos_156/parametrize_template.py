"""
Parametrize shifted-template maximal Sidon constructions for Erdős #156.

For a finite Sidon template B, define the relative blocker set

    W(B) = B union (B +/- Delta(B)) union Mid(B),

where Delta(B) is the set of positive pairwise differences and Mid(B) is the
set of integer midpoints of pairs in B.  If A = s + B, then the blocked points
for A are exactly s + W(B).  Thus A is maximal in [1,N] exactly when

    [1-s, N-s] subset W(B),

provided A itself lies in [1,N].

Usage:
  python3 erdos_156/parametrize_template.py
  python3 erdos_156/parametrize_template.py --B 0,40,60,61,63,67,96,112 --n-min 113 --n-max 145
  python3 erdos_156/parametrize_template.py --json
"""
from __future__ import annotations

import argparse
import json
from itertools import combinations
from typing import Iterable


DEFAULT_B = [0, 40, 60, 61, 63, 67, 96, 112]


def intervals(vals: Iterable[int]) -> list[list[int]]:
    xs = sorted(set(vals))
    if not xs:
        return []
    out = []
    start = prev = xs[0]
    for x in xs[1:]:
        if x == prev + 1:
            prev = x
        else:
            out.append([start, prev])
            start = prev = x
    out.append([start, prev])
    return out


def parse_template(raw: str) -> list[int]:
    vals = sorted(int(part.strip()) for part in raw.split(",") if part.strip())
    if len(vals) != len(set(vals)):
        raise argparse.ArgumentTypeError("template entries must be distinct")
    if not vals:
        raise argparse.ArgumentTypeError("template must be nonempty")
    return vals


def pair_differences(B: list[int]) -> list[int]:
    return sorted({b - a for a, b in combinations(sorted(B), 2)})


def is_sidon(B: list[int]) -> bool:
    diffs = [b - a for a, b in combinations(sorted(B), 2)]
    return len(diffs) == len(set(diffs))


def blocker_set(B: list[int]) -> dict:
    B = sorted(B)
    diffs = pair_differences(B)
    W = set(B)
    diff_blockers = set()
    midpoint_blockers = set()

    for b in B:
        for d in diffs:
            diff_blockers.add(b - d)
            diff_blockers.add(b + d)
    W.update(diff_blockers)

    for a, b in combinations(B, 2):
        if (a + b) % 2 == 0:
            midpoint_blockers.add((a + b) // 2)
    W.update(midpoint_blockers)

    runs = intervals(W)
    longest = max(runs, key=lambda ab: (ab[1] - ab[0] + 1, -abs(ab[0])))
    return {
        "B": B,
        "sidon": is_sidon(B),
        "differences": diffs,
        "midpoints": sorted(midpoint_blockers),
        "W": sorted(W),
        "W_size": len(W),
        "W_min": min(W),
        "W_max": max(W),
        "W_intervals": runs,
        "longest_interval": longest,
    }


def feasible_shifts(B: list[int], W: set[int], N: int) -> list[int]:
    min_b = min(B)
    max_b = max(B)
    lo = 1 - min_b
    hi = N - max_b
    shifts = []
    for s in range(lo, hi + 1):
        if all((x - s) in W for x in range(1, N + 1)):
            shifts.append(s)
    return shifts


def interval_sufficient_shifts(B: list[int], interval: list[int], N: int) -> list[int]:
    """Shifts certified only by one consecutive interval [L,R] inside W(B)."""
    min_b = min(B)
    max_b = max(B)
    L, R = interval
    lo = max(1 - min_b, N - R)
    hi = min(N - max_b, 1 - L)
    return list(range(lo, hi + 1)) if lo <= hi else []


def summarize(B: list[int], n_min: int, n_max: int) -> dict:
    data = blocker_set(B)
    W = set(data["W"])
    longest = data["longest_interval"]
    by_N = []
    for N in range(n_min, n_max + 1):
        shifts = feasible_shifts(B, W, N)
        interval_shifts = interval_sufficient_shifts(B, longest, N)
        by_N.append({
            "N": N,
            "feasible_shifts": shifts,
            "interval_sufficient_shifts": interval_shifts,
            "example_A": [shifts[0] + b for b in B] if shifts else None,
        })

    covered_Ns = [row["N"] for row in by_N if row["feasible_shifts"]]
    interval_Ns = [row["N"] for row in by_N if row["interval_sufficient_shifts"]]
    data.update({
        "N_min": n_min,
        "N_max": n_max,
        "feasible_by_N": by_N,
        "covered_Ns": covered_Ns,
        "interval_certified_Ns": interval_Ns,
    })
    return data


def compact_ranges(vals: Iterable[int]) -> str:
    parts = []
    for lo, hi in intervals(vals):
        parts.append(str(lo) if lo == hi else f"{lo}-{hi}")
    return ", ".join(parts) if parts else "-"


def print_text(data: dict) -> None:
    B = data["B"]
    L, R = data["longest_interval"]
    max_b = max(B)
    print(f"B = {B}")
    print(f"Sidon: {data['sidon']}")
    print(f"Delta(B) = {data['differences']}")
    print(f"|W(B)| = {data['W_size']}, support = [{data['W_min']}, {data['W_max']}]")
    print(f"Longest consecutive interval in W(B): [{L}, {R}] (length {R - L + 1})")
    print()
    print("Interval lemma for this template:")
    print(f"  max(1, N-{R}) <= s <= min({1 - L}, N-{max_b})")
    print("  Any integer s in that range gives A=s+B maximal in [1,N].")
    print()
    print(f"N covered in scan: {compact_ranges(data['covered_Ns'])}")
    print(f"N certified by longest interval alone: {compact_ranges(data['interval_certified_Ns'])}")
    print()
    print("N : feasible shifts (longest-interval shifts)")
    for row in data["feasible_by_N"]:
        shifts = row["feasible_shifts"]
        interval_shifts = row["interval_sufficient_shifts"]
        if shifts or interval_shifts:
            print(f"{row['N']:3d}: {shifts} ({interval_shifts})")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--B", type=parse_template, default=DEFAULT_B,
                        help="comma-separated template, e.g. 0,40,60,61,63,67,96,112")
    parser.add_argument("--n-min", type=int, default=113)
    parser.add_argument("--n-max", type=int, default=145)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    if args.n_min > args.n_max:
        parser.error("--n-min must be at most --n-max")

    data = summarize(args.B, args.n_min, args.n_max)
    if args.json:
        # Avoid dumping every point of W by default-sized scans?  It is small here
        # and useful for independent checking, so keep it explicit.
        print(json.dumps(data, indent=2))
    else:
        print_text(data)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
