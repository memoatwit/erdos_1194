"""
Search dense-core-plus-anchor shifted-template architectures for Erdős #156.

This combines two ideas:

1. Generate many seed templates from compact Sidon cores placed at different
   offsets, then complete them with anchors by a small inner beam search.
2. Run the shifted-template beam extension from the best seeds, scoring by
   blocker interval length divided by k^3.

This is meant to test whether the current [60,61,63,67] core is special, or
whether other dense-core-plus-anchor architectures give better normalized
coverage.

Usage:
  python3 erdos_156/search_template_architectures.py
  python3 erdos_156/search_template_architectures.py --core-size 5 --extend-k-max 16
"""
from __future__ import annotations

import argparse
import json
import os
from itertools import combinations
from types import SimpleNamespace
from typing import Iterable

import beam_template_search as beam


THIS_DIR = os.path.dirname(os.path.abspath(__file__))
RESULTS = os.path.join(THIS_DIR, "results")
KNOWN_SEED = [0, 40, 60, 61, 63, 67, 96, 112]


def intervals(vals: Iterable[int]) -> list[list[int]]:
    return beam.intervals(vals)


def compact_ranges(vals: Iterable[int]) -> str:
    parts = []
    for lo, hi in intervals(vals):
        parts.append(str(lo) if lo == hi else f"{lo}-{hi}")
    return ", ".join(parts) if parts else "-"


def longest_run(vals: Iterable[int]) -> int:
    runs = intervals(vals)
    return max((hi - lo + 1 for lo, hi in runs), default=0)


def core_patterns(core_size: int, core_span: int, limit: int) -> list[list[int]]:
    patterns = []
    for rest in combinations(range(1, core_span + 1), core_size - 1):
        C = [0, *rest]
        if not beam.is_sidon(C):
            continue
        diffs = sorted(set(beam.all_pair_diffs(C)))
        small = [d for d in diffs if d <= min(core_span, 12)]
        score = (
            longest_run(small),
            len(small),
            -C[-1],
            -sum(C),
        )
        patterns.append((score, C))
    patterns.sort(reverse=True)
    return [C for _score, C in patterns[:limit]]


def can_add_anywhere(B: list[int], x: int) -> bool:
    if x in B or x < 0:
        return False
    diffs = set(beam.all_pair_diffs(B))
    new_diffs = [abs(x - b) for b in B]
    if any(d == 0 for d in new_diffs):
        return False
    return len(new_diffs) == len(set(new_diffs)) and not (diffs & set(new_diffs))


def partial_metric(B: list[int]) -> tuple:
    """Score partial seed templates, before they necessarily cover an interval."""
    B = sorted(B)
    k = len(B)
    M = max(B)
    W = beam.blocker_set(B)
    best = None
    for L, R in beam.intervals(W):
        length = R - L + 1
        crosses_template = int(L <= 0 and R >= M)
        overlap = max(0, min(R, M) - max(L, 0) + 1)
        covered_end = R + 1 - L if crosses_template else 0
        row = (
            crosses_template,
            length / max(k ** 3, 1),
            covered_end / max(k ** 3, 1),
            overlap,
            length,
            -M,
        )
        if best is None or row > best:
            best = row
    return best if best is not None else (0, 0.0, 0.0, 0, 0, -M)


def complete_seed(base: list[int], seed_k: int, seed_max: int, inner_beam: int) -> list[list[int]]:
    states = [sorted(base)]
    while states and len(states[0]) < seed_k:
        seen = {}
        for B in states:
            for x in range(1, seed_max + 1):
                if not can_add_anywhere(B, x):
                    continue
                C = sorted(B + [x])
                key = tuple(C)
                score = partial_metric(C)
                current = seen.get(key)
                if current is None or score > current[0]:
                    seen[key] = (score, C)
        ranked = sorted(seen.values(), key=lambda item: item[0], reverse=True)
        states = [C for _score, C in ranked[:inner_beam]]
    return states


def generate_seeds(args: argparse.Namespace) -> list[dict]:
    seed_rows = []
    seen = set()
    patterns = core_patterns(args.core_size, args.core_span, args.core_limit)
    for pattern in patterns:
        max_offset = args.seed_max - pattern[-1]
        for offset in range(args.min_core_offset, max_offset + 1, args.offset_step):
            base = sorted({0, *[offset + x for x in pattern]})
            if len(base) != args.core_size + 1 or not beam.is_sidon(base):
                continue
            for seed in complete_seed(base, args.seed_k, args.seed_max, args.inner_beam):
                key = tuple(seed)
                if key in seen:
                    continue
                seen.add(key)
                metric = beam.template_metric(seed)
                if metric is None:
                    continue
                metric["seed_source"] = {
                    "core_pattern": pattern,
                    "core_offset": offset,
                    "base": base,
                }
                seed_rows.append(metric)

    if args.include_known_seed:
        metric = beam.template_metric(KNOWN_SEED)
        if metric is not None and tuple(KNOWN_SEED) not in seen:
            metric["seed_source"] = {"known_seed": True}
            seed_rows.append(metric)

    seed_rows.sort(key=beam.state_sort_key, reverse=True)
    return seed_rows[: args.seed_limit]


def beam_args_for_seed(seed: list[int], args: argparse.Namespace) -> SimpleNamespace:
    return SimpleNamespace(
        B=seed,
        k_max=args.extend_k_max,
        beam_width=args.extend_beam_width,
        x_factor=args.x_factor,
        x_window=args.x_window,
        require_overlap=not args.no_require_overlap,
    )


def run_seed_extensions(seeds: list[dict], args: argparse.Namespace) -> list[dict]:
    runs = []
    for index, seed_metric in enumerate(seeds):
        ns = beam_args_for_seed(seed_metric["B"], args)
        result = beam.run_beam(ns)
        last = result["best_by_k"][-1]
        best = result["best_overall"]
        runs.append({
            "seed_rank": index + 1,
            "seed": seed_metric,
            "last": last,
            "best_overall": best,
            "deepest_best_path": result["deepest_best_path"],
            "deepest_best_path_covered_union": result["deepest_best_path_covered_union"],
            "best_by_k": result["best_by_k"],
        })
    runs.sort(
        key=lambda row: (
            row["last"]["interval_length_over_k3"],
            row["last"]["covered_end_over_k3"],
            row["best_overall"]["interval_length_over_k3"],
        ),
        reverse=True,
    )
    return runs


def print_summary(seeds: list[dict], runs: list[dict], args: argparse.Namespace) -> None:
    print(f"Generated/ranked {len(seeds)} seed templates.")
    print("Top seeds:")
    for seed in seeds[: min(args.print_top, len(seeds))]:
        L, R = seed["interval"]
        a, b = seed["covered_N"]
        print(
            f"  k={seed['k']} score={seed['interval_length_over_k3']:.4f} "
            f"N={a}-{b} interval=[{L},{R}] B={seed['B']}"
        )

    print()
    print("Best extended runs:")
    print("rank seed_rank last_k last_N score end/k^3 union seed_B")
    for rank, run in enumerate(runs[: args.print_top], start=1):
        last = run["last"]
        a, b = last["covered_N"]
        union = ", ".join(
            f"{lo}-{hi}" if lo != hi else str(lo)
            for lo, hi in run["deepest_best_path_covered_union"]
        )
        print(
            f"{rank:4d} {run['seed_rank']:9d} {last['k']:6d} "
            f"{a:4d}-{b:<4d} {last['interval_length_over_k3']:.4f} "
            f"{last['covered_end_over_k3']:.4f} {union} {run['seed']['B']}"
        )


def write_json(obj: dict, path: str) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(obj, fh, indent=2)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed-k", type=int, default=8)
    parser.add_argument("--seed-max", type=int, default=180)
    parser.add_argument("--core-size", type=int, default=4)
    parser.add_argument("--core-span", type=int, default=12)
    parser.add_argument("--core-limit", type=int, default=32)
    parser.add_argument("--min-core-offset", type=int, default=20)
    parser.add_argument("--offset-step", type=int, default=3)
    parser.add_argument("--inner-beam", type=int, default=12)
    parser.add_argument("--seed-limit", type=int, default=16)
    parser.add_argument("--include-known-seed", action="store_true", default=True)
    parser.add_argument("--extend-k-max", type=int, default=16)
    parser.add_argument("--extend-beam-width", type=int, default=64)
    parser.add_argument("--x-factor", type=float, default=0.35)
    parser.add_argument("--x-window", type=int, default=320)
    parser.add_argument("--no-require-overlap", action="store_true")
    parser.add_argument("--print-top", type=int, default=8)
    parser.add_argument("--output", default=os.path.join(RESULTS, "template_architecture_search_156.json"))
    args = parser.parse_args()

    if args.seed_k <= args.core_size + 1:
        parser.error("--seed-k must leave room for at least one anchor beyond 0 and the core")
    if args.extend_k_max < args.seed_k:
        parser.error("--extend-k-max must be at least --seed-k")

    seeds = generate_seeds(args)
    runs = run_seed_extensions(seeds, args)
    output = {
        "args": vars(args),
        "seeds": seeds,
        "runs": runs,
    }
    write_json(output, args.output)
    print_summary(seeds, runs, args)
    print()
    print(f"Wrote {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
