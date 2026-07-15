#!/usr/bin/env python3
"""Aggregate the matched split-policy ablation and bootstrap paired effects."""

from __future__ import annotations

import argparse
import glob
import json
import random
import statistics
from collections import Counter, defaultdict
from functools import lru_cache
from pathlib import Path


POLICIES = (
    "deployed_witness_numeric",
    "witness_degree",
    "witness_random",
    "global_degree",
    "global_random",
)
BASELINE = "deployed_witness_numeric"


def percentile(values: list[float], probability: float) -> float:
    if not values:
        raise ValueError("cannot take percentile of an empty list")
    ordered = sorted(values)
    position = probability * (len(ordered) - 1)
    lower = int(position)
    upper = min(lower + 1, len(ordered) - 1)
    weight = position - lower
    return ordered[lower] * (1 - weight) + ordered[upper] * weight


def bootstrap_mean_ci(values: list[float], *, seed: int, samples: int) -> list[float]:
    rng = random.Random(seed)
    n = len(values)
    means = [sum(values[rng.randrange(n)] for _ in range(n)) / n for _ in range(samples)]
    return [percentile(means, 0.025), percentile(means, 0.975)]


def is_closed(row: dict) -> bool:
    return row["status"] in {"PRUNED_PREFIX_AP", "INFEASIBLE"}


def canonical_clauses(clauses: list[int] | tuple[int, ...]) -> tuple[int, ...]:
    kept = []
    for clause in sorted(set(clauses), key=lambda mask: (mask.bit_count(), mask)):
        if not any((smaller & clause) == smaller for smaller in kept):
            kept.append(clause)
    return tuple(kept)


def exact_prefix_survivors(N: int, variables: list[int], fixed_in: list[int]) -> dict:
    position = {value: index for index, value in enumerate(variables)}
    fixed = set(fixed_in)
    masks = []
    for middle in range(1, N + 1):
        for difference in range(1, min(middle - 1, N - middle) + 1):
            triple = (middle - difference, middle, middle + difference)
            if any(value not in position and value not in fixed for value in triple):
                continue
            mask = 0
            for value in triple:
                if value in position:
                    mask |= 1 << position[value]
            if mask == 0:
                return {"raw_assignments": 1 << len(variables), "survivors": 0, "forbidden_masks": 1}
            masks.append(mask)
    clauses = canonical_clauses(masks)

    @lru_cache(maxsize=None)
    def count(remaining: int, active: tuple[int, ...]) -> int:
        if any(mask == 0 for mask in active):
            return 0
        if not active:
            return 1 << remaining.bit_count()
        frequencies = Counter()
        for mask in active:
            bits = mask
            while bits:
                bit = bits & -bits
                frequencies[bit] += 1
                bits ^= bit
        bit = max(frequencies, key=lambda candidate: (frequencies[candidate], candidate))
        next_remaining = remaining & ~bit
        assign_zero = canonical_clauses([mask for mask in active if not mask & bit])
        assign_one = canonical_clauses([mask & ~bit if mask & bit else mask for mask in active])
        return count(next_remaining, assign_zero) + count(next_remaining, assign_one)

    raw = 1 << len(variables)
    survivors = count(raw - 1, clauses)
    return {
        "raw_assignments": raw,
        "survivors": survivors,
        "prefix_pruned": raw - survivors,
        "survival_rate": survivors / raw,
        "prefix_pruned_rate": 1 - survivors / raw,
        "forbidden_masks": len(clauses),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input-glob",
        default="results/baselines/split_policy_ablation/split_policy_idx*.jsonl",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("results/baselines/split_policy_ablation_summary.json"),
    )
    parser.add_argument("--bootstrap-samples", type=int, default=10_000)
    parser.add_argument("--bootstrap-seed", type=int, default=20260715)
    args = parser.parse_args()

    by_sample: dict[int, dict[str, dict]] = defaultdict(dict)
    files = sorted(glob.glob(args.input_glob))
    for filename in files:
        with open(filename, "r", encoding="utf-8") as fh:
            for line in fh:
                if not line.strip():
                    continue
                row = json.loads(line)
                sample_index = int(row["sample_index"])
                policy = row["policy"]
                if policy in by_sample[sample_index]:
                    raise ValueError(f"duplicate sample/policy row: {sample_index}/{policy}")
                by_sample[sample_index][policy] = row

    complete = {
        sample_index: rows
        for sample_index, rows in by_sample.items()
        if set(rows) == set(POLICIES)
    }
    summaries = {}
    for policy in POLICIES:
        rows = [complete[index][policy] for index in sorted(complete)]
        statuses = Counter(row["status"] for row in rows)
        seconds = [float(row.get("seconds", 0.0) or 0.0) for row in rows]
        solved_seconds = [
            float(row.get("seconds", 0.0) or 0.0)
            for row in rows
            if row["status"] != "PRUNED_PREFIX_AP"
        ]
        summaries[policy] = {
            "n": len(rows),
            "statuses": dict(sorted(statuses.items())),
            "prefix_pruned_rate": statuses["PRUNED_PREFIX_AP"] / len(rows),
            "closed_rate": sum(is_closed(row) for row in rows) / len(rows),
            "unknown_rate": statuses["UNKNOWN"] / len(rows),
            "total_seconds": sum(seconds),
            "mean_seconds_per_raw_assignment": statistics.mean(seconds),
            "median_seconds_per_raw_assignment": statistics.median(seconds),
            "p90_seconds_per_raw_assignment": percentile(seconds, 0.9),
            "median_seconds_if_solver_called": (
                statistics.median(solved_seconds) if solved_seconds else None
            ),
            "order_position_counts": dict(sorted(Counter(row["order_position"] for row in rows).items())),
        }
        if rows:
            summaries[policy]["exact_prefix_enumeration"] = exact_prefix_survivors(
                int(rows[0].get("N", 212)),
                [int(value) for value in rows[0]["split_variables"]],
                [1, 212],
            )

    paired = {}
    baseline_rows = complete
    for policy_index, policy in enumerate(POLICIES):
        if policy == BASELINE:
            continue
        close_differences = []
        time_differences = []
        for sample_index in sorted(baseline_rows):
            deployed = baseline_rows[sample_index][BASELINE]
            treatment = baseline_rows[sample_index][policy]
            close_differences.append(float(is_closed(treatment)) - float(is_closed(deployed)))
            time_differences.append(
                float(treatment.get("seconds", 0.0) or 0.0)
                - float(deployed.get("seconds", 0.0) or 0.0)
            )
        paired[policy] = {
            "versus": BASELINE,
            "closed_rate_difference": statistics.mean(close_differences),
            "closed_rate_difference_bootstrap_95ci": bootstrap_mean_ci(
                close_differences,
                seed=args.bootstrap_seed + policy_index,
                samples=args.bootstrap_samples,
            ),
            "mean_seconds_difference": statistics.mean(time_differences),
            "mean_seconds_difference_bootstrap_95ci": bootstrap_mean_ci(
                time_differences,
                seed=args.bootstrap_seed + 100 + policy_index,
                samples=args.bootstrap_samples,
            ),
        }

    result = {
        "input_glob": args.input_glob,
        "files": len(files),
        "observed_sample_count": len(by_sample),
        "complete_paired_sample_count": len(complete),
        "incomplete_sample_indices": sorted(set(by_sample) - set(complete)),
        "baseline_policy": BASELINE,
        "policy_summaries": summaries,
        "paired_effects": paired,
        "bootstrap_samples": args.bootstrap_samples,
        "bootstrap_seed": args.bootstrap_seed,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
