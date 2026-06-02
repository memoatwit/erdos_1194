"""
Aggregate per-chunk JSONL shards from the Phase-2 SLURM sweep.

After a Phase-2 SLURM array completes, each task wrote one JSONL shard under
`results/broad24/`.  Shards may contain either one chunk row or a contiguous
range of chunk rows.  This script concatenates them into a master JSONL and
reports:

  * total processed chunks,
  * status histogram,
  * still-missing chunk IDs in [chunk-start, chunk-end),
  * any UNKNOWN chunks that need a Phase-3 refinement.

It writes the master file and a TSV-style chunk-id report.

Usage:
  python3 r3_collect.py \
      --shard-dir results/broad24 \
      --chunk-start 575 --chunk-end 1574 \
      --out results/N212_K44_broad24_575_1574.jsonl \
      --missing-out results/N212_K44_missing_575_1574.txt \
      --unknown-out results/N212_K44_unknown_575_1574.txt
"""
from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path


def parse_chunk_list(path: Path) -> list[int]:
    text = path.read_text(encoding="utf-8").strip()
    if not text:
        return []
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        data = [
            token.strip()
            for token in text.replace(",", "\n").splitlines()
            if token.strip()
        ]
    if isinstance(data, dict):
        for key in ("chunk_ids", "chunks", "sample"):
            if key in data:
                data = data[key]
                break
        else:
            raise SystemExit(f"Could not find chunk list in {path}")
    out = []
    seen = set()
    for value in data:
        chunk_id = int(value)
        if chunk_id not in seen:
            seen.add(chunk_id)
            out.append(chunk_id)
    return out


def parse_jsonl(path: Path) -> list[dict]:
    rows = []
    if not path.exists():
        return rows
    with path.open("r", encoding="utf-8") as fh:
        for ln in fh:
            ln = ln.strip()
            if not ln:
                continue
            try:
                rows.append(json.loads(ln))
            except json.JSONDecodeError:
                continue
    return rows


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--shard-dir", type=Path, required=True)
    p.add_argument("--chunk-start", type=int, default=None)
    p.add_argument("--chunk-end", type=int, default=None,
                   help="exclusive upper bound")
    p.add_argument("--chunk-list", type=Path, default=None,
                   help="optional explicit JSON/newline/comma list of chunk IDs to collect")
    p.add_argument("--out", type=Path, required=True,
                   help="master JSONL output path")
    p.add_argument("--missing-out", type=Path, default=None)
    p.add_argument("--unknown-out", type=Path, default=None)
    p.add_argument("--shard-glob", default="*.jsonl")
    p.add_argument("--quiet", action="store_true")
    args = p.parse_args()
    if args.chunk_list:
        expected_ids = parse_chunk_list(args.chunk_list)
        if not expected_ids:
            raise SystemExit(f"No chunk IDs found in {args.chunk_list}")
    else:
        if args.chunk_start is None or args.chunk_end is None:
            raise SystemExit("--chunk-start and --chunk-end are required without --chunk-list")
        if args.chunk_end <= args.chunk_start:
            raise SystemExit("--chunk-end must be greater than --chunk-start")
        expected_ids = list(range(args.chunk_start, args.chunk_end))
    expected_set = set(expected_ids)

    args.out.parent.mkdir(parents=True, exist_ok=True)

    status_counts = Counter()
    seen_ids = set()
    missing = []
    unknown_ids = []
    n_rows_written = 0
    feasible_rows = []

    rows_by_id: dict[int, dict] = {}
    for shard in sorted(args.shard_dir.glob(args.shard_glob)):
        for row in parse_jsonl(shard):
            cid = row.get("chunk_id")
            if not isinstance(cid, int):
                if not args.quiet:
                    print(f"warning: row in {shard} has non-integer chunk_id={cid!r}")
                continue
            if cid not in expected_set:
                continue
            if cid in rows_by_id and not args.quiet:
                print(f"warning: duplicate row for chunk_id={cid}; keeping row from {shard}")
            rows_by_id[cid] = row

    with args.out.open("w", encoding="utf-8") as outfh:
        for cid in expected_ids:
            row = rows_by_id.get(cid)
            if row is None:
                missing.append(cid)
                continue
            seen_ids.add(cid)
            status = row.get("status", "UNKNOWN")
            status_counts[status] += 1
            if status == "UNKNOWN":
                unknown_ids.append(cid)
            if status == "FEASIBLE":
                feasible_rows.append(row)
            outfh.write(json.dumps(row, sort_keys=True) + "\n")
            n_rows_written += 1

    if args.missing_out:
        args.missing_out.write_text("\n".join(str(c) for c in missing) + ("\n" if missing else ""))
    if args.unknown_out:
        args.unknown_out.write_text("\n".join(str(c) for c in unknown_ids) + ("\n" if unknown_ids else ""))

    report = {
        "shard_dir": str(args.shard_dir),
        "chunk_range": [args.chunk_start, args.chunk_end] if not args.chunk_list else None,
        "chunk_list": str(args.chunk_list) if args.chunk_list else None,
        "chunk_ids_expected": len(expected_ids),
        "rows_written": n_rows_written,
        "chunk_ids_seen": len(seen_ids),
        "chunk_ids_missing": len(missing),
        "status_counts": dict(status_counts),
        "unknown_count": len(unknown_ids),
        "feasible_count": len(feasible_rows),
    }
    print(json.dumps(report, indent=2))

    if feasible_rows:
        print("\n*** FEASIBLE rows found — r_3(212) >= 44 ! ***")
        for r in feasible_rows[:3]:
            print(json.dumps(r, indent=2, default=str))
        return 0

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
