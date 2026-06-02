#!/usr/bin/env python3
"""
aggregate_verifications.py — collect drat-trim verification outputs.

The verifier arrays wrote rows into several places as the certificate cleanup
progressed:

  * results/sat_t1b_proofs/verification.jsonl
  * results/sat_t1b_proofs/verification_shards/
  * results/sat_t1b_proofs/verification_shards_4h/
  * results/sat_t1b_proofs/verification_shards_12h/
  * results/sat_t1b_proofs/verification_shards_final2_24h/

This script merges them into one canonical JSONL with a summary row first,
followed by the best row per chunk. "Best" means VERIFIED if available,
otherwise the most informative non-verified status. The summary row includes
an all_verified boolean for release checks.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any


T1B_UNSAT_CHUNK_IDS_ORDERED: list[int] = [
    14331,
    15357,
    24557,
    32251,
    32637,
    32735,
    36859,
    40943,
    63231,
    64319,
    65373,
    77311,
    81279,
    89838,
    93949,
    97782,
    110586,
    110587,
]

STATUS_PRIORITY = {
    "VERIFIED": 5,
    "NOT_VERIFIED": 4,
    "TIMEOUT": 3,
    "ERROR": 2,
    "MISSING_CNF": 1,
    "MISSING_DRAT": 1,
}


def read_rows_from_dir(shard_dir: Path, pattern: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not shard_dir.exists():
        return rows
    for path in sorted(shard_dir.glob(pattern)):
        rows.extend(read_rows_from_file(path))
    return rows


def read_rows_from_file(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not path.exists():
        return rows
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line:
            continue
        row = json.loads(line)
        row.setdefault("source_shard", str(path))
        if row.get("record_type") != "summary":
            rows.append(row)
    return rows


def choose_best_row(rows: list[dict[str, Any]]) -> dict[str, Any]:
    def score(row: dict[str, Any]) -> tuple[int, int, float]:
        status_score = STATUS_PRIORITY.get(str(row.get("status", "")), 0)
        has_lrat = 1 if has_true_lrat(row) else 0
        seconds = float(row.get("drat_trim_seconds", 0.0) or 0.0)
        return (status_score, has_lrat, seconds)

    return sorted(rows, key=score, reverse=True)[0]


def has_true_lrat(row: dict[str, Any]) -> bool:
    """Return True only for actual drat-trim -L LRAT artifacts.

    Early verifier runs used drat-trim lowercase -l while naming the target
    directory "lrat_*"; those files are trimmed DRAT lemmas, not LRAT. The
    final verifier pass uses uppercase -L and writes under lrat_final2_24h.
    """
    if int(row.get("lrat_bytes", 0) or 0) <= 0:
        return False
    if row.get("lrat_format") == "LRAT":
        return True
    path = str(row.get("lrat_path", ""))
    source = str(row.get("source_shard", ""))
    return "lrat_final2_24h" in path or "verification_shards_final2_24h" in source


def summarize(rows: list[dict[str, Any]], expected_chunks: list[int]) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    grouped: dict[int, list[dict[str, Any]]] = {}
    for row in rows:
        if "chunk_id" not in row:
            continue
        grouped.setdefault(int(row["chunk_id"]), []).append(row)

    by_chunk = {cid: choose_best_row(chunk_rows) for cid, chunk_rows in grouped.items()}

    expected = set(expected_chunks)
    seen = set(by_chunk)
    missing = sorted(expected - seen)
    unexpected = sorted(seen - expected)
    duplicate_chunks = sorted(cid for cid, chunk_rows in grouped.items() if len(chunk_rows) > 1)
    status_counts = Counter(str(row.get("status", "MISSING")) for row in by_chunk.values())

    verified_chunks = sorted(
        cid for cid, row in by_chunk.items() if row.get("status") == "VERIFIED"
    )
    not_verified_chunks = sorted(
        cid for cid, row in by_chunk.items() if row.get("status") != "VERIFIED"
    )
    lrat_chunks = sorted(
        cid
        for cid, row in by_chunk.items()
        if row.get("status") == "VERIFIED" and has_true_lrat(row)
    )
    legacy_lrat_field_chunks = sorted(
        cid
        for cid, row in by_chunk.items()
        if row.get("status") == "VERIFIED"
        and int(row.get("lrat_bytes", 0) or 0) > 0
        and not has_true_lrat(row)
    )

    total_drat_bytes = sum(int(row.get("drat_bytes", 0) or 0) for row in by_chunk.values())
    total_cnf_bytes = sum(int(row.get("cnf_bytes", 0) or 0) for row in by_chunk.values())
    total_lrat_bytes = sum(
        int(row.get("lrat_bytes", 0) or 0)
        for row in by_chunk.values()
        if has_true_lrat(row)
    )
    total_seconds = sum(
        float(row.get("drat_trim_seconds", 0.0) or 0.0) for row in by_chunk.values()
    )

    summary = {
        "record_type": "summary",
        "expected_count": len(expected_chunks),
        "source_row_count": len(rows),
        "unique_chunk_count": len(by_chunk),
        "all_expected_present": not missing,
        "all_verified": not missing and not unexpected and len(verified_chunks) == len(expected_chunks),
        "status_counts": dict(status_counts),
        "verified_count": len(verified_chunks),
        "verified_chunks": verified_chunks,
        "not_verified_chunks": not_verified_chunks,
        "missing_chunks": missing,
        "unexpected_chunks": unexpected,
        "duplicate_chunks": duplicate_chunks,
        "lrat_count": len(lrat_chunks),
        "lrat_chunks": lrat_chunks,
        "legacy_lrat_field_chunks": legacy_lrat_field_chunks,
        "lrat_note": (
            "lrat_count counts only actual drat-trim -L LRAT artifacts. "
            "legacy_lrat_field_chunks had lrat_bytes from earlier lowercase -l "
            "runs, which emitted trimmed DRAT lemmas rather than LRAT."
        ),
        "total_drat_trim_seconds": total_seconds,
        "total_cnf_bytes": total_cnf_bytes,
        "total_drat_bytes": total_drat_bytes,
        "total_lrat_bytes": total_lrat_bytes,
    }
    ordered_rows = [by_chunk[cid] for cid in sorted(by_chunk)]
    return summary, ordered_rows


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--shard-dir", type=Path, action="append", default=None)
    ap.add_argument("--input-jsonl", type=Path, action="append", default=None)
    ap.add_argument("--pattern", default="verify_idx*.jsonl")
    ap.add_argument(
        "--output",
        type=Path,
        default=Path("results/sat_t1b_proofs/verification.jsonl"),
    )
    ap.add_argument(
        "--summary-json",
        type=Path,
        default=Path("results/sat_t1b_proofs/verification_summary.json"),
    )
    args = ap.parse_args()

    if args.shard_dir is None and args.input_jsonl is None:
        args.input_jsonl = [Path("results/sat_t1b_proofs/verification.jsonl")]
        args.shard_dir = [
            Path("results/sat_t1b_proofs/verification_shards"),
            Path("results/sat_t1b_proofs/verification_shards_4h"),
            Path("results/sat_t1b_proofs/verification_shards_12h"),
            Path("results/sat_t1b_proofs/verification_shards_final2_24h"),
        ]

    rows: list[dict[str, Any]] = []
    for path in args.input_jsonl or []:
        rows.extend(read_rows_from_file(path))
    for shard_dir in args.shard_dir or []:
        rows.extend(read_rows_from_dir(shard_dir, args.pattern))
        if args.pattern != "*.jsonl":
            rows.extend(read_rows_from_dir(shard_dir, "*.jsonl"))
    summary, ordered_rows = summarize(rows, T1B_UNSAT_CHUNK_IDS_ORDERED)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w") as fh:
        fh.write(json.dumps(summary, sort_keys=True) + "\n")
        for row in ordered_rows:
            fh.write(json.dumps(row, sort_keys=True) + "\n")

    args.summary_json.parent.mkdir(parents=True, exist_ok=True)
    args.summary_json.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")

    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0 if summary["all_verified"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
