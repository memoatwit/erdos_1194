"""
Exact MILP solver for r_3(N), the maximum size of a 3-AP-free subset of [1..N].

This uses SciPy's HiGHS MILP backend.  It is the same mathematical encoding
planned for CP-SAT:

  binary x_i for i = 1..N
  maximize sum_i x_i
  x_a + x_b + x_c <= 2 for every 3-term arithmetic progression a,b,c

The solver's optimal status gives the upper bound; the selected variables give
an explicit witness for the lower bound.

Usage:
  python3 erdos_r3/r3_milp.py 80 --witness
  python3 erdos_r3/r3_milp.py --range 40 80 --oeis erdos_r3/results/b003002.txt
"""
from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import numpy as np
from scipy.optimize import Bounds, LinearConstraint, milp
from scipy.sparse import coo_array

from r3_verify import verify


def arithmetic_progressions(N: int) -> list[tuple[int, int, int]]:
    """Return all triples a<b<c in [1..N] with a+c=2b."""
    triples = []
    for b in range(1, N + 1):
        max_d = min(b - 1, N - b)
        for d in range(1, max_d + 1):
            triples.append((b - d, b, b + d))
    return triples


def ap_constraint_matrix(N: int, triples: list[tuple[int, int, int]]) -> coo_array:
    rows = []
    cols = []
    data = []
    for row, triple in enumerate(triples):
        for value in triple:
            rows.append(row)
            cols.append(value - 1)
            data.append(1.0)
    return coo_array((data, (rows, cols)), shape=(len(triples), N)).tocsr()


def load_oeis(path: Path) -> dict[int, int]:
    values = {}
    with path.open("r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            n_str, value_str = line.split()[:2]
            values[int(n_str)] = int(value_str)
    return values


def solve_r3_milp(
    N: int,
    *,
    time_limit: float | None = None,
    disp: bool = False,
    symmetry_break: bool = True,
) -> dict:
    triples = arithmetic_progressions(N)
    matrix = ap_constraint_matrix(N, triples)
    lower = np.full(len(triples), -np.inf)
    upper = np.full(len(triples), 2.0)

    constraints = [LinearConstraint(matrix, lower, upper)]
    if symmetry_break and N >= 2:
        # Reflection symmetry: i -> N+1-i.  Force x_1 >= x_N to cut the two
        # reflected copies of a solution family when they differ at the ends.
        sym = coo_array(([1.0, -1.0], ([0, 0], [0, N - 1])), shape=(1, N)).tocsr()
        constraints.append(LinearConstraint(sym, np.array([0.0]), np.array([np.inf])))

    c = -np.ones(N)
    options = {"disp": disp, "mip_rel_gap": 0.0}
    if time_limit is not None:
        options["time_limit"] = time_limit

    t0 = time.time()
    result = milp(
        c,
        integrality=np.ones(N),
        bounds=Bounds(np.zeros(N), np.ones(N)),
        constraints=constraints,
        options=options,
    )
    seconds = time.time() - t0

    selected: list[int] = []
    if result.x is not None:
        selected = [i + 1 for i, value in enumerate(result.x) if value >= 0.5]

    certifies_optimal = int(result.status) == 0
    size = len(selected)
    objective_bound = None
    if hasattr(result, "mip_dual_bound") and result.mip_dual_bound is not None:
        objective_bound = -float(result.mip_dual_bound)

    verification = verify(selected, N=N) if selected else None
    return {
        "N": N,
        "r_3": size if certifies_optimal else None,
        "best_size": size,
        "certifies_optimal": certifies_optimal,
        "solver_status": int(result.status),
        "solver_message": result.message,
        "solver_fun": float(result.fun) if result.fun is not None else None,
        "mip_gap": float(getattr(result, "mip_gap", 0.0) or 0.0),
        "objective_bound": objective_bound,
        "ap_constraints": len(triples),
        "seconds": round(seconds, 4),
        "witness": selected,
        "witness_verified": verification["ok"] if verification else False,
        "witness_report": verification,
    }


def compact_result(result: dict, include_witness: bool) -> dict:
    keys = [
        "N",
        "r_3",
        "best_size",
        "certifies_optimal",
        "solver_status",
        "mip_gap",
        "ap_constraints",
        "seconds",
        "witness_verified",
    ]
    out = {key: result[key] for key in keys}
    if include_witness:
        out["witness"] = result["witness"]
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("N", type=int, nargs="?")
    parser.add_argument("--range", type=int, nargs=2, metavar=("START", "END"))
    parser.add_argument("--time-limit", type=float, default=None)
    parser.add_argument("--no-symmetry-break", action="store_true")
    parser.add_argument("--witness", action="store_true")
    parser.add_argument("--oeis", type=Path, default=None)
    parser.add_argument("--output", type=Path, default=None)
    parser.add_argument("--disp", action="store_true")
    args = parser.parse_args()

    oeis = load_oeis(args.oeis) if args.oeis else {}
    Ns = range(args.range[0], args.range[1] + 1) if args.range else [args.N]
    if any(N is None for N in Ns):
        parser.error("specify N or --range START END")

    rows = []
    all_ok = True
    for N in Ns:
        result = solve_r3_milp(
            int(N),
            time_limit=args.time_limit,
            disp=args.disp,
            symmetry_break=not args.no_symmetry_break,
        )
        if int(N) in oeis:
            result["oeis"] = oeis[int(N)]
            result["matches_oeis"] = result["certifies_optimal"] and result["r_3"] == oeis[int(N)]
            all_ok = all_ok and result["matches_oeis"]
        elif not result["certifies_optimal"]:
            all_ok = False
        rows.append(result)
        compact = compact_result(result, include_witness=args.witness)
        if "oeis" in result:
            compact["oeis"] = result["oeis"]
            compact["matches_oeis"] = result["matches_oeis"]
        print(json.dumps(compact, indent=2))

    payload = rows[0] if len(rows) == 1 else {"results": rows}
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with args.output.open("w", encoding="utf-8") as fh:
            json.dump(payload, fh, indent=2)
            fh.write("\n")

    return 0 if all_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
