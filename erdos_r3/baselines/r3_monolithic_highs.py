#!/usr/bin/env python3
"""
r3_monolithic_highs.py — HiGHS MIP baseline on the full unsplit r_3(212)
decision instance (no witness-split pins).

Part of the monolithic-baseline experiment: what does each solver paradigm
do on the whole instance, without the cube-and-conquer split?

Usage (on Unity, via submit_baseline_highs.sbatch):
  python3 baselines/r3_monolithic_highs.py --windows --time-limit 86400 \
      --output results/baselines/highs_monolithic_win.json
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from r3_highs_attack import (  # noqa: E402
    arithmetic_progressions,
    build_and_solve,
    load_window_bounds,
)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--N", type=int, default=212)
    ap.add_argument("--K", type=int, default=44)
    ap.add_argument("--windows", action="store_true")
    ap.add_argument("--b-file", type=Path, default=Path("results/b003002.txt"))
    ap.add_argument("--time-limit", type=float, default=86400.0)
    ap.add_argument("--threads", type=int, default=8)
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()

    window_bounds = load_window_bounds(args.b_file) if args.windows else {}
    triples = arithmetic_progressions(args.N)

    t0 = time.time()
    result = build_and_solve(
        N=args.N,
        K=args.K,
        fixed_in=[1, args.N],  # endpoint forcing, same as the campaign model
        fixed_out=[],
        window_bounds=window_bounds,
        triples=triples,
        time_limit=args.time_limit,
        threads=args.threads,
        log=True,
    )
    result.update(
        {
            "experiment": "monolithic-baseline",
            "paradigm": "highs-mip",
            "windows": args.windows,
            "N": args.N,
            "K": args.K,
            "wall_seconds": time.time() - t0,
        }
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, default=str) + "\n")
    print(json.dumps(result, default=str))
    return 0


if __name__ == "__main__":
    sys.exit(main())
