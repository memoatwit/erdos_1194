#!/usr/bin/env python3
"""Generate an exact survivor count and sample for a depth-24 split policy."""

from __future__ import annotations

import argparse
import hashlib
import json
import random
from pathlib import Path


def arithmetic_progressions(N: int):
    for middle in range(1, N + 1):
        for difference in range(1, min(middle - 1, N - middle) + 1):
            yield middle - difference, middle, middle + difference


def global_degree_variables(N: int, count: int, excluded: set[int]) -> list[int]:
    degrees = {value: 0 for value in range(1, N + 1)}
    for triple in arithmetic_progressions(N):
        for value in triple:
            degrees[value] += 1
    center = (N + 1) / 2
    return sorted(
        (value for value in range(1, N + 1) if value not in excluded),
        key=lambda value: (-degrees[value], abs(value - center), value),
    )[:count]


def forbidden_masks(N: int, variables: list[int], fixed_in: set[int]) -> list[int]:
    position = {value: index for index, value in enumerate(variables)}
    masks = []
    for triple in arithmetic_progressions(N):
        if any(value not in position and value not in fixed_in for value in triple):
            continue
        mask = 0
        for value in triple:
            if value in position:
                mask |= 1 << position[value]
        if mask == 0:
            raise ValueError("fixed-in values already contain a 3-AP")
        masks.append(mask)
    kept = []
    for mask in sorted(set(masks), key=lambda value: (value.bit_count(), value)):
        if not any((smaller & mask) == smaller for smaller in kept):
            kept.append(mask)
    return kept


def enumerate_survivors(variable_count: int, masks: list[int]) -> list[int]:
    by_last_bit: list[list[int]] = [[] for _ in range(variable_count)]
    for mask in masks:
        by_last_bit[mask.bit_length() - 1].append(mask)
    survivors = []

    def visit(bit_index: int, raw_id: int) -> None:
        if bit_index == variable_count:
            survivors.append(raw_id)
            return
        selected = raw_id | (1 << bit_index)
        if not any((selected & mask) == mask for mask in by_last_bit[bit_index]):
            visit(bit_index + 1, selected)
        visit(bit_index + 1, raw_id)

    visit(0, 0)
    return survivors


def decode(raw_id: int, variables: list[int], endpoints: set[int]) -> tuple[list[int], list[int]]:
    fixed_in = set(endpoints)
    fixed_out = set()
    for bit_index, value in enumerate(variables):
        (fixed_in if (raw_id >> bit_index) & 1 else fixed_out).add(value)
    return sorted(fixed_in), sorted(fixed_out)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--N", type=int, default=212)
    parser.add_argument("--K", type=int, default=44)
    parser.add_argument("--split-count", type=int, default=24)
    parser.add_argument("--sample-size", type=int, default=100)
    parser.add_argument("--sample-seed", type=int, default=20260716)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--summary", type=Path, required=True)
    parser.add_argument(
        "--survivors-output",
        type=Path,
        help="Optional newline-delimited list of every surviving raw assignment ID",
    )
    args = parser.parse_args()

    endpoints = {1, args.N}
    variables = global_degree_variables(args.N, args.split_count, endpoints)
    masks = forbidden_masks(args.N, variables, endpoints)
    survivors = enumerate_survivors(args.split_count, masks)
    sampled = sorted(random.Random(args.sample_seed).sample(survivors, args.sample_size))
    split_hash = hashlib.sha256(
        json.dumps(variables, separators=(",", ":")).encode("ascii")
    ).hexdigest()
    # Canonicalize the optional full-cover artifact independently of the DFS
    # traversal order. The sampling population retains its historical order.
    survivor_text = "".join(f"{raw_id}\n" for raw_id in sorted(survivors))

    if args.survivors_output:
        args.survivors_output.parent.mkdir(parents=True, exist_ok=True)
        args.survivors_output.write_text(survivor_text, encoding="ascii")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8") as fh:
        for raw_id in sampled:
            fixed_in, fixed_out = decode(raw_id, variables, endpoints)
            row = {
                "chunk_id": raw_id,
                "raw_assignment_id": raw_id,
                "N": args.N,
                "K": args.K,
                "policy": "global_degree",
                "split_count": args.split_count,
                "split_variables": variables,
                "split_variables_sha256": split_hash,
                "fixed_in": fixed_in,
                "fixed_out": fixed_out,
                "sample_seed": args.sample_seed,
            }
            fh.write(json.dumps(row, sort_keys=True) + "\n")

    summary = {
        "N": args.N,
        "K": args.K,
        "policy": "global_degree",
        "split_count": args.split_count,
        "split_variables": variables,
        "split_variables_sha256": split_hash,
        "raw_assignment_count": 1 << args.split_count,
        "forbidden_mask_count": len(masks),
        "survivor_count": len(survivors),
        "survival_rate": len(survivors) / (1 << args.split_count),
        "survivor_raw_ids_sha256": hashlib.sha256(
            survivor_text.encode("ascii")
        ).hexdigest(),
        "sample_size": args.sample_size,
        "sample_seed": args.sample_seed,
        "sample_raw_ids_sha256": hashlib.sha256(
            json.dumps(sampled, separators=(",", ":")).encode("ascii")
        ).hexdigest(),
        "sample_jsonl": str(args.output),
    }
    args.summary.parent.mkdir(parents=True, exist_ok=True)
    args.summary.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
