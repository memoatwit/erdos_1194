#!/usr/bin/env python3
"""Extract a status-defined residual from a completed chunk survey."""

from __future__ import annotations

import argparse
import glob
import hashlib
import json
from collections import Counter
from pathlib import Path


def read_jsonl(path: Path) -> list[dict]:
    rows: list[dict] = []
    for line_no, line in enumerate(path.read_text().splitlines(), 1):
        if not line.strip():
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError as exc:
            raise SystemExit(f"{path}:{line_no}: invalid JSON: {exc}") from exc
    return rows


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def atomic_write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp")
    temporary.write_text(text)
    temporary.replace(path)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--results-glob", required=True)
    parser.add_argument("--status", default="UNKNOWN")
    parser.add_argument("--expected-source", type=int)
    parser.add_argument("--expected-selected", type=int)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--summary", type=Path, required=True)
    args = parser.parse_args()

    source_rows = read_jsonl(args.source)
    if args.expected_source is not None and len(source_rows) != args.expected_source:
        raise SystemExit(
            f"expected {args.expected_source} source rows, found {len(source_rows)}"
        )

    source_by_id: dict[int, dict] = {}
    for row in source_rows:
        chunk_id = int(row["chunk_id"])
        if chunk_id in source_by_id:
            raise SystemExit(f"duplicate source chunk_id {chunk_id}")
        source_by_id[chunk_id] = row

    result_files = sorted(Path(path) for path in glob.glob(args.results_glob))
    if not result_files:
        raise SystemExit(f"no result files match {args.results_glob!r}")

    result_by_id: dict[int, dict] = {}
    for path in result_files:
        for row in read_jsonl(path):
            chunk_id = int(row["chunk_id"])
            if chunk_id in result_by_id:
                raise SystemExit(f"duplicate result chunk_id {chunk_id}")
            result_by_id[chunk_id] = row

    missing = sorted(set(source_by_id) - set(result_by_id))
    extra = sorted(set(result_by_id) - set(source_by_id))
    if missing or extra:
        raise SystemExit(
            f"source/result mismatch: missing={missing[:10]} extra={extra[:10]}"
        )

    target_status = args.status.upper()
    selected = [
        row
        for row in source_rows
        if str(result_by_id[int(row["chunk_id"])].get("status", "")).upper()
        == target_status
    ]
    if args.expected_selected is not None and len(selected) != args.expected_selected:
        raise SystemExit(
            f"expected {args.expected_selected} selected rows, found {len(selected)}"
        )

    output_text = "".join(json.dumps(row, sort_keys=True) + "\n" for row in selected)
    atomic_write(args.out, output_text)

    counts = Counter(
        str(row.get("status", "MISSING")).upper() for row in result_by_id.values()
    )
    summary = {
        "source": str(args.source),
        "source_rows": len(source_rows),
        "result_glob": args.results_glob,
        "result_files": len(result_files),
        "result_rows": len(result_by_id),
        "status_counts": dict(sorted(counts.items())),
        "selected_status": target_status,
        "selected_rows": len(selected),
        "selected_chunk_ids": [int(row["chunk_id"]) for row in selected],
        "output": str(args.out),
        "output_sha256": sha256(args.out),
    }
    atomic_write(args.summary, json.dumps(summary, indent=2, sort_keys=True) + "\n")
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
