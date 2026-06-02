"""
Generate an alternative 43-point 3-AP-free witness for the r_3(212) campaign.

The witness-ensemble pilot needs a second 43-set that is structurally distinct
from the current witness.  This script solves a CP-SAT feasibility model with
the usual 3-AP and optional window-cardinality constraints, plus a Hamming
distance constraint from a base witness:

  d_H(A, A_base) >= threshold.

It writes both the witness JSON and the witness values sorted in the same
degree order used by the depth-24 split runner.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

LOCAL_DEPS = Path(__file__).resolve().parent / ".deps"
if LOCAL_DEPS.exists():
    sys.path.insert(0, str(LOCAL_DEPS))

from ortools.sat.python import cp_model  # noqa: E402

from r3_cpsat import (  # noqa: E402
    add_reflection_lex_break,
    arithmetic_progressions,
    load_int_set,
    load_window_bounds,
)
from r3_verify import verify  # noqa: E402


def degree_ranked_values(N: int) -> list[int]:
    degrees = {i: 0 for i in range(1, N + 1)}
    for triple in arithmetic_progressions(N):
        for value in triple:
            degrees[value] += 1
    center = (N + 1) / 2
    return sorted(range(1, N + 1), key=lambda value: (-degrees[value], abs(value - center), value))


def hamming_distance(A: list[int], B: list[int], N: int) -> int:
    a = set(A)
    b = set(B)
    return sum((i in a) != (i in b) for i in range(1, N + 1))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--N", type=int, default=212)
    parser.add_argument("--target", type=int, default=43)
    parser.add_argument("--base-witness", type=Path, required=True)
    parser.add_argument("--hamming-min", type=int, default=20)
    parser.add_argument("--window-bounds", type=Path, default=None)
    parser.add_argument("--time-limit", type=float, default=900)
    parser.add_argument("--workers", type=int, default=8)
    parser.add_argument("--branch-value", choices=["min", "max"], default="min")
    parser.add_argument("--fixed-search", action="store_true")
    parser.add_argument("--no-symmetry-break", action="store_true")
    parser.add_argument("--log", action="store_true")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--split-vars-output", type=Path, required=True)
    args = parser.parse_args()

    N = args.N
    base = load_int_set(args.base_witness)
    if len(base) != args.target:
        raise SystemExit(f"base witness has size {len(base)}, expected {args.target}")

    model = cp_model.CpModel()
    x = [model.NewBoolVar(f"x_{i}") for i in range(1, N + 1)]

    triples = arithmetic_progressions(N)
    for a, b, c in triples:
        model.Add(x[a - 1] + x[b - 1] + x[c - 1] <= 2)

    window_constraints = 0
    if args.window_bounds:
        bounds = load_window_bounds(args.window_bounds)
        for L in range(2, N + 1):
            rL = bounds.get(L)
            if rL is None or rL >= L or rL >= args.target:
                continue
            for start in range(0, N - L + 1):
                model.Add(sum(x[start:start + L]) <= rL)
                window_constraints += 1

    model.Add(sum(x) == args.target)
    base_set = set(base)
    hamming_terms = []
    for value in range(1, N + 1):
        var = x[value - 1]
        hamming_terms.append(1 - var if value in base_set else var)
    model.Add(sum(hamming_terms) >= args.hamming_min)

    if not args.no_symmetry_break:
        add_reflection_lex_break(model, x)

    ranked = degree_ranked_values(N)
    ordered_vars = [x[value - 1] for value in ranked]
    value_strategy = cp_model.SELECT_MAX_VALUE if args.branch_value == "max" else cp_model.SELECT_MIN_VALUE
    model.AddDecisionStrategy(ordered_vars, cp_model.CHOOSE_FIRST, value_strategy)

    solver = cp_model.CpSolver()
    solver.parameters.num_search_workers = args.workers
    solver.parameters.random_seed = 1194
    solver.parameters.log_search_progress = args.log
    if args.fixed_search:
        solver.parameters.search_branching = cp_model.FIXED_SEARCH
    if args.time_limit is not None:
        solver.parameters.max_time_in_seconds = args.time_limit

    t0 = time.time()
    status = solver.Solve(model)
    seconds = time.time() - t0
    status_name = solver.StatusName(status)
    if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        payload = {
            "N": N,
            "target": args.target,
            "base_witness": base,
            "hamming_min": args.hamming_min,
            "status": status_name,
            "seconds": round(seconds, 4),
            "branches": solver.NumBranches(),
            "conflicts": solver.NumConflicts(),
            "window_constraints": window_constraints,
        }
        failure_path = args.output.with_name(args.output.name + ".failed")
        failure_path.parent.mkdir(parents=True, exist_ok=True)
        failure_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(payload, indent=2))
        print(f"Non-feasible status written to {failure_path}", file=sys.stderr)
        return 1

    A = [i + 1 for i, var in enumerate(x) if solver.Value(var)]
    report = verify(A, N=N)
    if not report.get("ok"):
        raise SystemExit(f"solver returned non-verified witness: {report}")

    split_vars = [value for value in ranked if value in set(A)]
    payload = {
        "N": N,
        "target": args.target,
        "A": A,
        "size": len(A),
        "base_witness": base,
        "hamming_distance": hamming_distance(A, base, N),
        "hamming_min": args.hamming_min,
        "status": status_name,
        "seconds": round(seconds, 4),
        "branches": solver.NumBranches(),
        "conflicts": solver.NumConflicts(),
        "wall_time": round(solver.WallTime(), 4),
        "ap_constraints": len(triples),
        "window_constraints": window_constraints,
        "witness_verified": report.get("ok"),
        "witness_report": report,
    }

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.split_vars_output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    args.split_vars_output.write_text(json.dumps(split_vars, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": status_name,
        "size": len(A),
        "hamming_distance": payload["hamming_distance"],
        "seconds": payload["seconds"],
        "output": str(args.output),
        "split_vars_output": str(args.split_vars_output),
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
