#!/usr/bin/env python3
"""Select a deterministic solve-time-stratified proof sample."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path


QUANTILES = (0.0, 0.2, 0.4, 0.6, 0.8, 1.0)


def read_jsonl(path: Path) -> list[dict]:
    with path.open(encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sample", type=Path, required=True)
    parser.add_argument("--results", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--summary", type=Path, required=True)
    args = parser.parse_args()

    samples = {int(row["chunk_id"]): row for row in read_jsonl(args.sample)}
    results = {int(row["chunk_id"]): row for row in read_jsonl(args.results)}
    if samples.keys() != results.keys() or len(samples) != 100:
        raise SystemExit("sample/results chunk IDs do not form the same 100-row population")
    urgent = [row for row in results.values() if row.get("status") == "SAT"]
    if urgent:
        raise SystemExit(f"urgent SAT rows present: {[row['chunk_id'] for row in urgent]}")

    closed = sorted(
        (row for row in results.values() if row.get("status") == "UNSAT"),
        key=lambda row: (float(row["solver_seconds"]), int(row["chunk_id"])),
    )
    if len(closed) != 79:
        raise SystemExit(f"expected 79 UNSAT rows, found {len(closed)}")

    selected = []
    used = set()
    for quantile in QUANTILES:
        rank = int(math.floor(quantile * (len(closed) - 1) + 0.5))
        result = closed[rank]
        chunk_id = int(result["chunk_id"])
        if chunk_id in used:
            raise SystemExit("quantile selection produced a duplicate chunk")
        used.add(chunk_id)
        row = dict(samples[chunk_id])
        row.update(
            {
                "selection_quantile": quantile,
                "selection_rank": rank,
                "prior_status": result["status"],
                "prior_solver_seconds": result["solver_seconds"],
                "prior_cnf_sha256": result["cnf_sha256"],
            }
        )
        selected.append(row)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8") as handle:
        for row in selected:
            handle.write(json.dumps(row, sort_keys=True) + "\n")

    summary = {
        "population_count": len(samples),
        "closed_population_count": len(closed),
        "selection_method": "nearest ranks at fixed solve-time quantiles",
        "selection_quantiles": list(QUANTILES),
        "selected": [
            {
                "chunk_id": row["chunk_id"],
                "quantile": row["selection_quantile"],
                "rank": row["selection_rank"],
                "prior_solver_seconds": row["prior_solver_seconds"],
                "prior_cnf_sha256": row["prior_cnf_sha256"],
            }
            for row in selected
        ],
        "sample_sha256": sha256(args.sample),
        "results_sha256": sha256(args.results),
        "output_sha256": sha256(args.output),
    }
    args.summary.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
