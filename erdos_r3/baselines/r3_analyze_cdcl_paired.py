#!/usr/bin/env python3
"""Aggregate the hardware-matched native CaDiCaL/kissat comparison."""

from __future__ import annotations

import argparse
import glob
import json
import math
import random
import statistics
from pathlib import Path
from typing import Any


def percentile(values: list[float], probability: float) -> float:
    ordered = sorted(values)
    position = probability * (len(ordered) - 1)
    lower = int(position)
    upper = min(lower + 1, len(ordered) - 1)
    weight = position - lower
    return ordered[lower] * (1.0 - weight) + ordered[upper] * weight


def time_summary(values: list[float]) -> dict[str, float]:
    return {
        "sum": sum(values),
        "mean": statistics.mean(values),
        "median": statistics.median(values),
        "p90": percentile(values, 0.9),
        "max": max(values),
    }


def geometric_mean(values: list[float]) -> float:
    return math.exp(statistics.mean(math.log(value) for value in values))


def load_single_json_rows(pattern: str) -> list[dict[str, Any]]:
    rows = []
    for name in sorted(glob.glob(pattern)):
        lines = [line for line in Path(name).read_text().splitlines() if line.strip()]
        if len(lines) != 1:
            raise ValueError(f"expected one JSON row in {name}, found {len(lines)}")
        rows.append(json.loads(lines[0]))
    return rows


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--input-glob",
        default="results/baselines/cdcl_paired_amd7763/paired_idx*.json",
    )
    parser.add_argument(
        "--output",
        default="results/baselines/cdcl_paired_amd7763_summary.json",
    )
    parser.add_argument(
        "--cadical-glob",
        default="results/baselines/cdcl_paired_amd7763/cadical_idx*.jsonl",
    )
    parser.add_argument(
        "--kissat-glob",
        default="results/baselines/cdcl_paired_amd7763/kissat_idx*.jsonl",
    )
    parser.add_argument("--expected", type=int, default=20)
    parser.add_argument("--bootstrap-samples", type=int, default=10_000)
    parser.add_argument("--bootstrap-seed", type=int, default=20260715)
    args = parser.parse_args()

    rows: list[dict[str, Any]] = []
    for name in sorted(glob.glob(args.input_glob)):
        rows.append(json.loads(Path(name).read_text()))
    indices = [int(row["array_index"]) for row in rows]
    if len(indices) != len(set(indices)):
        raise ValueError("duplicate array indices")
    if len(rows) != args.expected:
        raise ValueError(f"expected {args.expected} paired rows, found {len(rows)}")
    if sorted(indices) != list(range(args.expected)):
        raise ValueError("paired array indices are not 0..expected-1")
    if any(row["cadical_status"] == "SAT" or row["kissat_status"] == "SAT" for row in rows):
        raise ValueError("SAT row requires immediate witness verification")

    cadical_rows = load_single_json_rows(args.cadical_glob)
    kissat_rows = load_single_json_rows(args.kissat_glob)
    if len(cadical_rows) != args.expected or len(kissat_rows) != args.expected:
        raise ValueError("raw solver-row count does not match expected paired count")
    for pair, cadical_row, kissat_row in zip(rows, cadical_rows, kissat_rows):
        chunk_ids = {pair["chunk_id"], cadical_row["chunk_id"], kissat_row["chunk_id"]}
        hashes = {pair["cnf_sha256"], cadical_row["cnf_sha256"], kissat_row["cnf_sha256"]}
        if len(chunk_ids) != 1 or len(hashes) != 1:
            raise ValueError(f"paired formula mismatch at array index {pair['array_index']}")
        if cadical_row["status"] != pair["cadical_status"]:
            raise ValueError(f"CaDiCaL status mismatch at array index {pair['array_index']}")
        if kissat_row["status"] != pair["kissat_status"]:
            raise ValueError(f"kissat status mismatch at array index {pair['array_index']}")

    cadical = [float(row["cadical_seconds"]) for row in rows]
    kissat = [float(row["kissat_seconds"]) for row in rows]
    ratios = [c / k for c, k in zip(cadical, kissat)]
    rng = random.Random(args.bootstrap_seed)
    bootstrap = []
    for _ in range(args.bootstrap_samples):
        sample = [ratios[rng.randrange(len(ratios))] for _ in ratios]
        bootstrap.append(geometric_mean(sample))

    by_order: dict[str, list[float]] = {}
    for row, ratio in zip(rows, ratios):
        label = "-then-".join(row["order"])
        by_order.setdefault(label, []).append(ratio)

    output = {
        "hardware_constraint": "amd7763",
        "paired_instances": len(rows),
        "raw_solver_rows_verified_cnf_hash_equality": True,
        "raw_solver_rows_match_pair_summaries": True,
        "statuses": {
            "cadical": {status: sum(row["cadical_status"] == status for row in rows) for status in sorted({row["cadical_status"] for row in rows})},
            "kissat": {status: sum(row["kissat_status"] == status for row in rows) for status in sorted({row["kissat_status"] for row in rows})},
        },
        "solver_seconds": {
            "cadical": time_summary(cadical),
            "kissat": time_summary(kissat),
        },
        "paired_speed": {
            "ratio_definition": "cadical_seconds / kissat_seconds",
            "kissat_faster": sum(k < c for c, k in zip(cadical, kissat)),
            "cadical_faster": sum(c < k for c, k in zip(cadical, kissat)),
            "ties": sum(c == k for c, k in zip(cadical, kissat)),
            "geometric_mean_ratio": geometric_mean(ratios),
            "geometric_mean_ratio_bootstrap_95ci": [
                percentile(bootstrap, 0.025),
                percentile(bootstrap, 0.975),
            ],
            "median_ratio": statistics.median(ratios),
            "order_strata_geometric_mean_ratio": {
                order: geometric_mean(values) for order, values in sorted(by_order.items())
            },
        },
        "bootstrap_samples": args.bootstrap_samples,
        "bootstrap_seed": args.bootstrap_seed,
    }
    Path(args.output).write_text(json.dumps(output, indent=2, sort_keys=True) + "\n")
    print(json.dumps(output, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
