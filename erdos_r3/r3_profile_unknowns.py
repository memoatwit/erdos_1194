"""
Profile UNKNOWN chunks from an r_3 split-search JSONL file.

The intended use is after a broad CP-SAT sweep:

  python3 r3_profile_unknowns.py results/N212_K44_broad24_window_11575_111574.jsonl \
      --chunk-start 11575 --chunk-end 111575 \
      --sample-out results/N212_K44_window100k_refine_sample100.json

It reports status counts, solver-time histograms, chunk-id clustering, and
which split-variable pins are enriched among UNKNOWN rows.  With --sample-out it
also writes a bounded refinement sample: slowest UNKNOWN chunks first, then a
reproducible random sample from the remaining UNKNOWNs.
"""
from __future__ import annotations

import argparse
import json
import math
import random
from collections import Counter, defaultdict
from pathlib import Path
from statistics import mean, median


def read_rows(path: Path) -> list[dict]:
    rows: list[dict] = []
    with path.open("r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            rows.append(json.loads(line))
    return rows


def seconds(row: dict) -> float:
    try:
        return float(row.get("seconds", 0.0) or 0.0)
    except (TypeError, ValueError):
        return 0.0


def quantiles(values: list[float]) -> dict:
    if not values:
        return {}
    ordered = sorted(values)

    def q(frac: float) -> float:
        index = min(len(ordered) - 1, max(0, round(frac * (len(ordered) - 1))))
        return ordered[index]

    return {
        "min": round(ordered[0], 4),
        "p25": round(q(0.25), 4),
        "median": round(median(ordered), 4),
        "p75": round(q(0.75), 4),
        "p90": round(q(0.90), 4),
        "p99": round(q(0.99), 4),
        "max": round(ordered[-1], 4),
        "mean": round(mean(ordered), 4),
    }


def contiguous_runs(values: list[int]) -> list[tuple[int, int, int]]:
    if not values:
        return []
    values = sorted(values)
    runs = []
    start = prev = values[0]
    for value in values[1:]:
        if value == prev + 1:
            prev = value
            continue
        runs.append((start, prev, prev - start + 1))
        start = prev = value
    runs.append((start, prev, prev - start + 1))
    return runs


def bucket_counts(rows: list[dict], *, chunk_start: int, chunk_end: int, bins: int) -> list[dict]:
    width = max(1, math.ceil((chunk_end - chunk_start) / bins))
    buckets = []
    for i in range(bins):
        a = chunk_start + i * width
        b = min(chunk_end, a + width)
        if a >= chunk_end:
            break
        buckets.append({"start": a, "end": b, "total": 0, "UNKNOWN": 0, "INFEASIBLE": 0, "FEASIBLE": 0})
    for row in rows:
        cid = int(row.get("chunk_id", -1))
        if cid < chunk_start or cid >= chunk_end:
            continue
        index = min(len(buckets) - 1, (cid - chunk_start) // width)
        status = row.get("status", "UNKNOWN")
        buckets[index]["total"] += 1
        if status in buckets[index]:
            buckets[index][status] += 1
    for bucket in buckets:
        total = bucket["total"]
        bucket["unknown_rate"] = round(bucket["UNKNOWN"] / total, 6) if total else 0.0
    return buckets


def pin_enrichment(rows: list[dict], unknown_rows: list[dict]) -> list[dict]:
    if not rows:
        return []
    split_variables = rows[0].get("split_variables", []) or []
    all_by_value = {value: Counter() for value in split_variables}
    unk_by_value = {value: Counter() for value in split_variables}

    def add(row: dict, target: dict[int, Counter]) -> None:
        fixed_in = set(int(x) for x in row.get("assignment_fixed_in", []))
        fixed_out = set(int(x) for x in row.get("assignment_fixed_out", []))
        for value in split_variables:
            if value in fixed_in:
                target[value]["in"] += 1
            elif value in fixed_out:
                target[value]["out"] += 1

    for row in rows:
        add(row, all_by_value)
    for row in unknown_rows:
        add(row, unk_by_value)

    total_unknown_rate = len(unknown_rows) / len(rows) if rows else 0.0
    out = []
    for value in split_variables:
        all_counts = all_by_value[value]
        unk_counts = unk_by_value[value]
        in_total = all_counts["in"]
        out_total = all_counts["out"]
        in_rate = (unk_counts["in"] / in_total) if in_total else 0.0
        out_rate = (unk_counts["out"] / out_total) if out_total else 0.0
        out.append({
            "value": value,
            "unknown_if_in": round(in_rate, 6),
            "unknown_if_out": round(out_rate, 6),
            "gap": round(in_rate - out_rate, 6),
            "unknown_in": unk_counts["in"],
            "unknown_out": unk_counts["out"],
            "all_in": in_total,
            "all_out": out_total,
            "baseline_unknown_rate": round(total_unknown_rate, 6),
        })
    out.sort(key=lambda item: abs(item["gap"]), reverse=True)
    return out


def make_sample(
    unknown_rows: list[dict],
    *,
    sample_size: int,
    slowest_count: int,
    seed: int,
) -> list[int]:
    slowest_rows = sorted(unknown_rows, key=lambda row: (seconds(row), int(row["chunk_id"])), reverse=True)
    selected = [int(row["chunk_id"]) for row in slowest_rows[:slowest_count]]
    selected_set = set(selected)
    remaining = [int(row["chunk_id"]) for row in unknown_rows if int(row["chunk_id"]) not in selected_set]
    rng = random.Random(seed)
    rng.shuffle(remaining)
    selected.extend(remaining[: max(0, sample_size - len(selected))])
    return selected[:sample_size]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("jsonl", type=Path)
    parser.add_argument("--chunk-start", type=int, default=None)
    parser.add_argument("--chunk-end", type=int, default=None)
    parser.add_argument("--bins", type=int, default=20)
    parser.add_argument("--cap-seconds", type=float, default=60.0)
    parser.add_argument("--top", type=int, default=15)
    parser.add_argument("--sample-out", type=Path, default=None)
    parser.add_argument("--sample-size", type=int, default=100)
    parser.add_argument("--slowest-count", type=int, default=20)
    parser.add_argument("--seed", type=int, default=1194)
    args = parser.parse_args()

    rows = read_rows(args.jsonl)
    if not rows:
        raise SystemExit(f"No rows read from {args.jsonl}")

    chunk_ids = [int(row["chunk_id"]) for row in rows if "chunk_id" in row]
    chunk_start = args.chunk_start if args.chunk_start is not None else min(chunk_ids)
    chunk_end = args.chunk_end if args.chunk_end is not None else max(chunk_ids) + 1

    status_counts = Counter(row.get("status", "UNKNOWN") for row in rows)
    unknown_rows = [row for row in rows if row.get("status") == "UNKNOWN"]
    feasible_rows = [row for row in rows if row.get("status") == "FEASIBLE"]

    by_status_seconds = defaultdict(list)
    for row in rows:
        by_status_seconds[row.get("status", "UNKNOWN")].append(seconds(row))

    unknown_ids = [int(row["chunk_id"]) for row in unknown_rows]
    runs = contiguous_runs(unknown_ids)
    runs.sort(key=lambda run: run[2], reverse=True)

    capped_unknowns = [
        int(row["chunk_id"]) for row in unknown_rows
        if seconds(row) >= args.cap_seconds * 0.98
    ]

    sample = []
    if args.sample_out:
        sample = make_sample(
            unknown_rows,
            sample_size=args.sample_size,
            slowest_count=args.slowest_count,
            seed=args.seed,
        )
        args.sample_out.parent.mkdir(parents=True, exist_ok=True)
        args.sample_out.write_text(json.dumps(sample, indent=2) + "\n", encoding="utf-8")

    summary = {
        "path": str(args.jsonl),
        "chunk_range": [chunk_start, chunk_end],
        "rows": len(rows),
        "status_counts": dict(status_counts),
        "unknown_rate": round(len(unknown_rows) / len(rows), 6),
        "feasible_count": len(feasible_rows),
        "seconds_by_status": {
            status: quantiles(values)
            for status, values in sorted(by_status_seconds.items())
        },
        "unknowns_at_cap": {
            "threshold": round(args.cap_seconds * 0.98, 3),
            "count": len(capped_unknowns),
            "fraction_of_unknowns": round(len(capped_unknowns) / len(unknown_rows), 6) if unknown_rows else 0.0,
        },
        "unknown_runs": {
            "run_count": len(runs),
            "top_runs": [
                {"start": a, "end": b, "length": length}
                for a, b, length in runs[: args.top]
            ],
        },
        "bucket_counts": bucket_counts(rows, chunk_start=chunk_start, chunk_end=chunk_end, bins=args.bins),
        "pin_enrichment_top": pin_enrichment(rows, unknown_rows)[: args.top],
    }
    if sample:
        summary["sample"] = {
            "path": str(args.sample_out),
            "size": len(sample),
            "slowest_count": args.slowest_count,
            "seed": args.seed,
            "chunk_ids": sample,
        }

    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
