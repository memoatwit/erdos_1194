#!/usr/bin/env python3
"""
extract_t1b_residual20.py — filter the 45-chunk T1 residual file down to the
20 chunks that survived the 8-hour HiGHS longwall audit (T1b hard core).

Reads the recap300-residual45 file, writes a JSONL with only the T1b rows.
Order is preserved from the input file. The 20 chunk IDs are the audited
hard core from Unity job 58782313.

Usage:
  python3 extract_t1b_residual20.py \
      --input  results/N212_K44_broad24_recap300_residual45.jsonl \
      --output results/N212_K44_broad24_recap300_residual_t1b20.jsonl
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


# Audited from Unity job 58782313, 2026-05-25.
# These are the 20 chunks that remained UNKNOWN after the full 8-hour HiGHS
# audit with dual bound still pinned at 0.0.
T1B_CHUNK_IDS: set[int] = {
    14331,
    15357,
    24557,
    32251,
    32637,
    32735,
    36859,
    40943,
    40959,
    48895,
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
}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--input",
        type=Path,
        default=Path("results/N212_K44_broad24_recap300_residual45.jsonl"),
    )
    ap.add_argument(
        "--output",
        type=Path,
        default=Path("results/N212_K44_broad24_recap300_residual_t1b20.jsonl"),
    )
    args = ap.parse_args()

    rows = [
        json.loads(line) for line in args.input.read_text().splitlines() if line.strip()
    ]
    print(f"[load] {len(rows)} rows from {args.input}", file=sys.stderr)

    selected = [r for r in rows if r.get("chunk_id") in T1B_CHUNK_IDS]
    selected_ids = {r["chunk_id"] for r in selected}
    missing = T1B_CHUNK_IDS - selected_ids
    if missing:
        print(
            f"[warn] {len(missing)} T1b chunk IDs were not found in input: "
            f"{sorted(missing)}",
            file=sys.stderr,
        )

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w") as fh:
        for row in selected:
            fh.write(json.dumps(row) + "\n")
    print(f"[done] wrote {len(selected)} rows to {args.output}", file=sys.stderr)
    return 0 if not missing else 1


if __name__ == "__main__":
    sys.exit(main())
