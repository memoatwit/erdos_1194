#!/usr/bin/env python3
"""Optimization-form HiGHS diagnostic for pinned r_3 chunks.

Unlike the campaign's earlier zero-objective feasibility model, this program
maximizes sum_i x_i. It solves the continuous LP relaxation first and then the
binary MIP, making the reported LP optimum and MIP dual bound meaningful upper
bounds for the target cardinality.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
import time
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from r3_highs_attack import arithmetic_progressions, load_window_bounds  # noqa: E402


def finite_or_none(value: float) -> float | None:
    value = float(value)
    return value if math.isfinite(value) else None


def solve_model(
    *,
    N: int,
    target: int,
    fixed_in: list[int],
    fixed_out: list[int],
    triples: list[tuple[int, int, int]],
    window_bounds: dict[int, int],
    integer: bool,
    time_limit: float,
    threads: int,
) -> dict[str, Any]:
    import highspy

    try:
        highspy.Highs.resetGlobalScheduler()
    except Exception:
        pass
    h = highspy.Highs()
    h.silent()
    inf = highspy.kHighsInf

    pinned_in = set(fixed_in) | {1, N}
    pinned_out = set(fixed_out)
    if pinned_in & pinned_out:
        return {"status": "INVALID", "reason": "fixed_in intersects fixed_out"}

    for value in range(1, N + 1):
        if value in pinned_in:
            lb = ub = 1.0
        elif value in pinned_out:
            lb = ub = 0.0
        else:
            lb, ub = 0.0, 1.0
        h.addVar(lb, ub)

    indices = list(range(N))
    h.changeColsCost(N, indices, [1.0] * N)
    h.changeObjectiveSense(highspy.ObjSense.kMaximize)

    for a, b, c in triples:
        h.addRow(-inf, 2.0, 3, [a - 1, b - 1, c - 1], [1.0, 1.0, 1.0])

    windows_added = 0
    for length, bound in sorted(window_bounds.items()):
        if length < 2 or length > N or bound >= length:
            continue
        for start in range(0, N - length + 1):
            cols = list(range(start, start + length))
            h.addRow(-inf, float(bound), length, cols, [1.0] * length)
            windows_added += 1

    if integer:
        h.changeColsIntegrality(
            N, indices, [highspy.HighsVarType.kInteger] * N
        )

    h.setOptionValue("time_limit", float(time_limit))
    h.setOptionValue("threads", int(threads))
    h.setOptionValue("presolve", "on")
    h.setOptionValue("mip_min_logging_interval", 60.0)

    started = time.time()
    h.run()
    elapsed = time.time() - started
    info = h.getInfo()
    status_text = h.modelStatusToString(h.getModelStatus())
    solution = h.getSolution()

    objective = finite_or_none(info.objective_function_value)
    upper_bound = (
        finite_or_none(info.mip_dual_bound) if integer else objective
    )
    certifies_no_target = bool(
        "Infeasible" in status_text
        or (upper_bound is not None and upper_bound < target - 1e-7)
    )
    witness = []
    if integer and objective is not None and solution.value_valid:
        witness = [i + 1 for i, value in enumerate(solution.col_value) if value > 0.5]

    return {
        "status": status_text,
        "integer": integer,
        "seconds": round(elapsed, 3),
        "objective": objective,
        "upper_bound": upper_bound,
        "certifies_no_target": certifies_no_target,
        "target": target,
        "mip_nodes": int(info.mip_node_count) if integer else None,
        "mip_gap": finite_or_none(info.mip_gap) if integer else None,
        "windows_added": windows_added,
        "ap_constraints": len(triples),
        "witness": witness,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--array-index", type=int, required=True)
    parser.add_argument("--N", type=int, default=212)
    parser.add_argument("--target", type=int, default=44)
    parser.add_argument("--window-bounds", type=Path, required=True)
    parser.add_argument("--windows", action="store_true")
    parser.add_argument("--lp-time-limit", type=float, default=600.0)
    parser.add_argument("--mip-time-limit", type=float, default=7200.0)
    parser.add_argument("--threads", type=int, default=8)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    rows = [json.loads(line) for line in args.input.read_text().splitlines() if line.strip()]
    if not 0 <= args.array_index < len(rows):
        raise SystemExit(f"array index {args.array_index} outside 0..{len(rows)-1}")
    row = rows[args.array_index]
    fixed_in = [int(v) for v in row.get("fixed_in", [])]
    fixed_out = [int(v) for v in row.get("fixed_out", [])]
    triples = arithmetic_progressions(args.N)
    windows = load_window_bounds(args.window_bounds) if args.windows else {}

    lp = solve_model(
        N=args.N,
        target=args.target,
        fixed_in=fixed_in,
        fixed_out=fixed_out,
        triples=triples,
        window_bounds=windows,
        integer=False,
        time_limit=args.lp_time_limit,
        threads=args.threads,
    )
    mip = solve_model(
        N=args.N,
        target=args.target,
        fixed_in=fixed_in,
        fixed_out=fixed_out,
        triples=triples,
        window_bounds=windows,
        integer=True,
        time_limit=args.mip_time_limit,
        threads=args.threads,
    )
    payload = {
        "experiment": "highs-optimization-diagnostic",
        "chunk_id": int(row["chunk_id"]),
        "N": args.N,
        "target": args.target,
        "windows": args.windows,
        "fixed_in_count": len(fixed_in),
        "fixed_out_count": len(fixed_out),
        "lp": lp,
        "mip": mip,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2) + "\n")
    print(json.dumps(payload, indent=2))
    return 1 if mip.get("witness") and len(mip["witness"]) >= args.target else 0


if __name__ == "__main__":
    raise SystemExit(main())
