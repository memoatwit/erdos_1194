#!/usr/bin/env python3
"""Validate and summarize the paired global-degree survivor experiment."""

from __future__ import annotations

import argparse
import glob
import json
import math
import statistics
from pathlib import Path
from typing import Any


def load_jsonl_files(pattern: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for name in sorted(glob.glob(pattern)):
        with open(name, encoding="utf-8") as handle:
            rows.extend(json.loads(line) for line in handle if line.strip())
    return rows


def unique_by_id(rows: list[dict[str, Any]], label: str) -> dict[int, dict[str, Any]]:
    result: dict[int, dict[str, Any]] = {}
    for row in rows:
        chunk_id = int(row["chunk_id"])
        if chunk_id in result:
            raise ValueError(f"{label}: duplicate chunk_id {chunk_id}")
        result[chunk_id] = row
    return result


def wilson(successes: int, trials: int, z: float = 1.959963984540054) -> list[float] | None:
    if trials == 0:
        return None
    proportion = successes / trials
    denominator = 1.0 + z * z / trials
    center = (proportion + z * z / (2.0 * trials)) / denominator
    radius = z * math.sqrt(
        proportion * (1.0 - proportion) / trials + z * z / (4.0 * trials * trials)
    ) / denominator
    return [max(0.0, center - radius), min(1.0, center + radius)]


def summarize(rows: dict[int, dict[str, Any]], expected_ids: set[int]) -> dict[str, Any]:
    observed_ids = set(rows)
    unexpected = sorted(observed_ids - expected_ids)
    missing = sorted(expected_ids - observed_ids)
    if unexpected:
        raise ValueError(f"unexpected chunk IDs: {unexpected}")

    statuses: dict[str, int] = {}
    seconds: list[float] = []
    for row in rows.values():
        status = str(row.get("status", "MISSING"))
        statuses[status] = statuses.get(status, 0) + 1
        seconds.append(float(row.get("solver_seconds", row.get("seconds", 0.0)) or 0.0))

    closed = sum(statuses.get(status, 0) for status in ("UNSAT", "INFEASIBLE"))
    ordered = sorted(seconds)
    return {
        "expected": len(expected_ids),
        "observed": len(rows),
        "complete": not missing,
        "missing_chunk_ids": missing,
        "statuses": statuses,
        "closed": closed,
        "closed_rate": closed / len(rows) if rows else None,
        "closed_rate_wilson_95ci": wilson(closed, len(rows)),
        "solver_seconds": {
            "sum": sum(seconds),
            "mean": statistics.mean(seconds) if seconds else None,
            "median": statistics.median(seconds) if seconds else None,
            "p90_nearest_rank": ordered[max(0, math.ceil(0.9 * len(ordered)) - 1)] if ordered else None,
            "max": max(seconds) if seconds else None,
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--sample", required=True)
    parser.add_argument("--cpsat-glob", required=True)
    parser.add_argument("--kissat-glob", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--expected", type=int, default=100)
    args = parser.parse_args()

    sample_rows = load_jsonl_files(args.sample)
    sample = unique_by_id(sample_rows, "sample")
    if len(sample) != args.expected:
        raise ValueError(f"sample: expected {args.expected} rows, found {len(sample)}")
    expected_ids = set(sample)

    cpsat = unique_by_id(load_jsonl_files(args.cpsat_glob), "cpsat")
    kissat = unique_by_id(load_jsonl_files(args.kissat_glob), "kissat")
    urgent = [
        {"arm": arm, "chunk_id": chunk_id, "status": row.get("status")}
        for arm, rows in (("cpsat", cpsat), ("kissat", kissat))
        for chunk_id, row in rows.items()
        if row.get("status") in ("SAT", "FEASIBLE")
    ]

    output = {
        "sample_count": len(sample),
        "sample_seed": next(iter(sample.values())).get("sample_seed"),
        "split_variables_sha256": next(iter(sample.values())).get("split_variables_sha256"),
        "urgent_feasible_rows": urgent,
        "cpsat": summarize(cpsat, expected_ids),
        "kissat": summarize(kissat, expected_ids),
    }
    Path(args.output).write_text(json.dumps(output, indent=2, sort_keys=True) + "\n")
    print(json.dumps(output, indent=2, sort_keys=True))
    if urgent:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
