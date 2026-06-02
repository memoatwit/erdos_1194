"""
Greedily extend shifted-template chains for Erdős #156.

Starting from a Sidon template B, this searches for one new mark x > max(B)
that keeps B union {x} Sidon and whose relative blocker set W(B union {x})
contains a consecutive interval large enough to overlap the previous covered
N-range.  The default objective is to maximize the new covered endpoint.

This is an experiment, not a proof engine.  Its purpose is to make the
shifted-template continuation reproducible and to track whether N/k^3 is
stabilizing or decaying.

Usage:
  python3 erdos_156/extend_template_chain.py
  python3 erdos_156/extend_template_chain.py --k-max 20 --top 8
"""
from __future__ import annotations

import argparse
import json
import os
from itertools import combinations
from typing import Iterable


THIS_DIR = os.path.dirname(os.path.abspath(__file__))
RESULTS = os.path.join(THIS_DIR, "results")
DEFAULT_B = [0, 40, 60, 61, 63, 67, 96, 112]


def parse_template(raw: str) -> list[int]:
    vals = sorted(int(part.strip()) for part in raw.split(",") if part.strip())
    if len(vals) != len(set(vals)):
        raise argparse.ArgumentTypeError("template entries must be distinct")
    if not vals:
        raise argparse.ArgumentTypeError("template must be nonempty")
    if min(vals) != 0:
        raise argparse.ArgumentTypeError("template must be normalized with min 0")
    return vals


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


def all_pair_diffs(B: list[int]) -> list[int]:
    return [b - a for a, b in combinations(sorted(B), 2)]


def is_sidon(B: list[int]) -> bool:
    diffs = all_pair_diffs(B)
    return len(diffs) == len(set(diffs))


def can_append(B: list[int], x: int, existing_diffs: set[int] | None = None) -> bool:
    if x <= max(B) or x in B:
        return False
    if existing_diffs is None:
        existing_diffs = set(all_pair_diffs(B))
    new_diffs = [x - b for b in B]
    return len(new_diffs) == len(set(new_diffs)) and not (existing_diffs & set(new_diffs))


def blocker_set(B: list[int]) -> set[int]:
    B = sorted(B)
    diffs = sorted(set(all_pair_diffs(B)))
    W = set(B)
    for b in B:
        for d in diffs:
            W.add(b - d)
            W.add(b + d)
    for a, b in combinations(B, 2):
        if (a + b) % 2 == 0:
            W.add((a + b) // 2)
    return W


def best_admissible_interval(B: list[int]) -> dict | None:
    """Return the best interval [L,R] in W(B) that certifies shifted coverage."""
    M = max(B)
    W = blocker_set(B)
    candidates = []
    for L, R in intervals(W):
        if L <= 0 and R >= M:
            end = R + 1 - L
            candidates.append({
                "interval": [L, R],
                "length": R - L + 1,
                "covered_N": [M + 1, end],
                "W_size": len(W),
            })
    if not candidates:
        return None
    return max(candidates, key=lambda row: (row["covered_N"][1], row["length"], -abs(row["interval"][0])))


def evaluate_candidate(B: list[int], x: int, prev_end: int) -> dict | None:
    C = sorted(B + [x])
    info = best_admissible_interval(C)
    if info is None:
        return None
    start, end = info["covered_N"]
    if start > prev_end + 1:
        return None
    k = len(C)
    return {
        "x": x,
        "B": C,
        "k": k,
        "max_B": max(C),
        "interval": info["interval"],
        "interval_length": info["length"],
        "covered_N": info["covered_N"],
        "covered_end_over_k3": end / (k ** 3),
        "interval_length_over_k3": info["length"] / (k ** 3),
        "W_size": info["W_size"],
    }


def initial_row(B: list[int]) -> dict:
    info = best_admissible_interval(B)
    if info is None:
        raise ValueError("initial template has no admissible blocker interval")
    k = len(B)
    end = info["covered_N"][1]
    return {
        "x": None,
        "B": B,
        "k": k,
        "max_B": max(B),
        "interval": info["interval"],
        "interval_length": info["length"],
        "covered_N": info["covered_N"],
        "covered_end_over_k3": end / (k ** 3),
        "interval_length_over_k3": info["length"] / (k ** 3),
        "W_size": info["W_size"],
    }


def extend_chain(B: list[int], k_max: int, top: int) -> dict:
    if not is_sidon(B):
        raise ValueError("initial template is not Sidon")

    chain = [initial_row(B)]
    top_candidates_by_step = []

    while len(chain[-1]["B"]) < k_max:
        current = chain[-1]
        current_B = current["B"]
        prev_end = current["covered_N"][1]
        existing_diffs = set(all_pair_diffs(current_B))
        candidates = []
        for x in range(max(current_B) + 1, prev_end + 1):
            if not can_append(current_B, x, existing_diffs):
                continue
            candidate = evaluate_candidate(current_B, x, prev_end)
            if candidate is not None:
                candidates.append(candidate)

        candidates.sort(
            key=lambda row: (
                row["covered_N"][1],
                row["interval_length"],
                -row["max_B"],
            ),
            reverse=True,
        )
        top_candidates_by_step.append({
            "from_k": len(current_B),
            "previous_covered_end": prev_end,
            "candidate_count": len(candidates),
            "top_candidates": candidates[:top],
        })
        if not candidates:
            break
        chain.append(candidates[0])

    return {
        "initial_B": B,
        "k_max_requested": k_max,
        "chain": chain,
        "top_candidates_by_step": top_candidates_by_step,
    }


def write_json(data: dict, path: str) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2)


def print_table(data: dict) -> None:
    print("k  x_added  maxB  interval       covered_N  end/k^3  gain")
    print("-- ------- ----- -------------- ---------- -------- -----")
    prev_end = None
    for row in data["chain"]:
        k = row["k"]
        x = "-" if row["x"] is None else str(row["x"])
        M = row["max_B"]
        L, R = row["interval"]
        start, end = row["covered_N"]
        gain = "-" if prev_end is None else str(end - prev_end)
        prev_end = end
        print(
            f"{k:2d} {x:>7} {M:5d} "
            f"[{L:4d},{R:4d}] {start:4d}-{end:<4d} "
            f"{row['covered_end_over_k3']:.4f} {gain:>5}"
        )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--B", type=parse_template, default=DEFAULT_B)
    parser.add_argument("--k-max", type=int, default=20)
    parser.add_argument("--top", type=int, default=8)
    parser.add_argument("--output", default=os.path.join(RESULTS, "template_chain_156_greedy.json"))
    args = parser.parse_args()

    if args.k_max < len(args.B):
        parser.error("--k-max must be at least len(B)")
    if args.top < 1:
        parser.error("--top must be positive")

    data = extend_chain(args.B, args.k_max, args.top)
    write_json(data, args.output)
    print_table(data)
    print()
    print(f"Wrote {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
