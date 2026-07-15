#!/usr/bin/env python3
"""Run the campaign CP-SAT configuration on one row of an input JSONL."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

R3_DIR = Path(__file__).resolve().parents[1]
if str(R3_DIR) not in sys.path:
    sys.path.insert(0, str(R3_DIR))

from r3_cpsat import load_int_set, load_window_bounds, solve_r3_cpsat  # noqa: E402


def load_row(path: Path, index: int) -> dict:
    with path.open("r", encoding="utf-8") as fh:
        for row_index, line in enumerate(fh):
            if row_index == index:
                return json.loads(line)
    raise IndexError(f"row index {index} is outside {path}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--array-index", type=int, required=True)
    parser.add_argument("--N", type=int, default=212)
    parser.add_argument("--K", type=int, default=44)
    parser.add_argument("--time-limit", type=float, default=60.0)
    parser.add_argument("--workers", type=int, default=8)
    parser.add_argument(
        "--hint", type=Path, default=R3_DIR / "results/N212_K43_witness.json"
    )
    parser.add_argument(
        "--window-bounds", type=Path, default=R3_DIR / "results/b003002.txt"
    )
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    source = load_row(args.input, args.array_index)
    result = solve_r3_cpsat(
        args.N,
        decision_size=args.K,
        time_limit=args.time_limit,
        workers=args.workers,
        symmetry_break=True,
        fixed_in=[int(value) for value in source["fixed_in"]],
        fixed_out=[int(value) for value in source["fixed_out"]],
        hint=load_int_set(args.hint),
        branch_order="degree",
        branch_value="min",
        fixed_search=True,
        window_bounds=load_window_bounds(args.window_bounds),
    )
    if result["is_feasible_for_decision_size"]:
        status = "FEASIBLE"
    elif result["solver_status_name"] == "INFEASIBLE":
        status = "INFEASIBLE"
    else:
        status = "UNKNOWN"
    row = {
        **source,
        "array_index": args.array_index,
        "experiment": "global-degree-survivor-cpsat",
        "status": status,
        "solver_status_name": result["solver_status_name"],
        "seconds": result["seconds"],
        "wall_time": result["wall_time"],
        "branches": result["branches"],
        "conflicts": result["conflicts"],
        "window_constraints": result["window_constraints"],
        "workers": args.workers,
        "time_limit": args.time_limit,
        "witness": result["witness"] if status == "FEASIBLE" else [],
        "witness_verified": result["witness_verified"],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(row, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"chunk_id": source["chunk_id"], "status": status, "seconds": row["seconds"]}))
    return 2 if status == "FEASIBLE" else 0


if __name__ == "__main__":
    raise SystemExit(main())
