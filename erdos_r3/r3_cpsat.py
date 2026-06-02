"""
CP-SAT solver for r_3(N), the maximum size of a 3-AP-free subset of [1..N].

The model is:

  x_i in {0,1} for i = 1..N
  maximize sum_i x_i
  x_a + x_b + x_c <= 2 for every 3-term arithmetic progression a,b,c

If OR-Tools is not globally installed, this script loads the local dependency
folder created by:

  python3 -m pip install --target erdos_r3/.deps ortools

Usage:
  python3 erdos_r3/r3_cpsat.py 80 --oeis erdos_r3/results/b003002.txt --witness
  python3 erdos_r3/r3_cpsat.py --range 40 80 --oeis erdos_r3/results/b003002.txt
  python3 erdos_r3/r3_cpsat.py 212 --decision-size 44 --fix-in fixed.json --hint hint.json
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

from r3_verify import verify  # noqa: E402


def arithmetic_progressions(N: int) -> list[tuple[int, int, int]]:
    triples = []
    for b in range(1, N + 1):
        max_d = min(b - 1, N - b)
        for d in range(1, max_d + 1):
            triples.append((b - d, b, b + d))
    return triples


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


def load_int_set(path: Path) -> list[int]:
    """Load a candidate/fixed set from a JSON list or dict with A/witness keys."""
    with path.open("r", encoding="utf-8") as fh:
        raw = json.load(fh)
    if isinstance(raw, dict):
        for key in ("A", "witness", "fixed_in", "fixed_out"):
            if key in raw:
                raw = raw[key]
                break
    if not isinstance(raw, list):
        raise ValueError(f"{path} must be a JSON list or contain A/witness/fixed_in/fixed_out")
    return sorted({int(x) for x in raw})


def validate_int_set(values: list[int], N: int, label: str) -> list[int]:
    bad = [x for x in values if x < 1 or x > N]
    if bad:
        raise ValueError(f"{label} contains values outside [1..{N}]: {bad[:10]}")
    return sorted(set(values))


def load_window_bounds(path: Path | None) -> dict[int, int]:
    """Load OEIS A003002 b-file (lines of "n r_3(n)") into {n: r_3(n)} dict.

    Returns empty dict if path is None or file missing.  Lines starting with
    '#' or blank are ignored.
    """
    if path is None or not Path(path).exists():
        return {}
    bounds: dict[int, int] = {}
    with Path(path).open("r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            try:
                a, b = line.split()
                bounds[int(a)] = int(b)
            except ValueError:
                continue
    return bounds


def solve_r3_cpsat(
    N: int,
    *,
    time_limit: float | None = None,
    workers: int = 8,
    symmetry_break: bool = True,
    log: bool = False,
    decision_size: int | None = None,
    fixed_in: list[int] | None = None,
    fixed_out: list[int] | None = None,
    hint: list[int] | None = None,
    branch_order: str = "natural",
    branch_value: str = "max",
    fixed_search: bool = False,
    window_bounds: dict[int, int] | None = None,
    window_bounds_min_length: int = 2,
    pair_clauses_window: tuple[int, int] | None = None,
) -> dict:
    model = cp_model.CpModel()
    x = [model.NewBoolVar(f"x_{i}") for i in range(1, N + 1)]
    fixed_in = validate_int_set(fixed_in or [], N, "fixed_in")
    fixed_out = validate_int_set(fixed_out or [], N, "fixed_out")
    hint = validate_int_set(hint or [], N, "hint")
    overlap = sorted(set(fixed_in) & set(fixed_out))
    if overlap:
        raise ValueError(f"fixed_in and fixed_out overlap: {overlap[:10]}")

    triples = arithmetic_progressions(N)
    for a, b, c in triples:
        model.Add(x[a - 1] + x[b - 1] + x[c - 1] <= 2)

    # Window-cardinality constraints derived from OEIS A003002 r_3(L) values.
    # For any window [a, a+L-1] of length L, |A ∩ window| ≤ r_3(L).
    # We add the non-trivial ones (r_3(L) < L) over all valid window positions.
    window_constraints_added = 0
    if window_bounds:
        for L in range(max(2, window_bounds_min_length), N + 1):
            rL = window_bounds.get(L)
            if rL is None or rL >= L:
                continue
            if decision_size is not None and rL >= decision_size:
                # Cannot bind on a window of size <= decision_size's value.
                continue
            for start in range(0, N - L + 1):
                # sum x[start..start+L-1] <= rL
                model.Add(sum(x[start:start + L]) <= rL)
                window_constraints_added += 1

    for value in fixed_in:
        model.Add(x[value - 1] == 1)
    for value in fixed_out:
        model.Add(x[value - 1] == 0)

    # Targeted pair-AND propagation clauses.  For each midpoint m in the
    # requested window, define an explicit BoolVar pair[a,c] = x[a] AND x[c]
    # for every (a,c) with a+c = 2m, 1 <= a < m < c <= N, and add the
    # implication pair[a,c] -> NOT x[m].  This is mathematically redundant
    # with the existing triple constraint x[a] + x[c] + x[m] <= 2, but it
    # gives CP-SAT an extra Tseitin propagator that can be useful in
    # structurally hard pockets (e.g. when the middle witness pins are all
    # forced OUT).  Empirical experiment; not guaranteed to help.
    pair_clauses_added = 0
    if pair_clauses_window is not None:
        lo, hi = pair_clauses_window
        lo = max(1, int(lo))
        hi = min(N, int(hi))
        for m in range(lo, hi + 1):
            a_min = max(1, 2 * m - N)
            for a in range(a_min, m):
                c = 2 * m - a
                if c <= m or c > N:
                    continue
                pair_var = model.NewBoolVar(f"pair_{a}_{c}")
                # Linear Tseitin: pair = x[a] AND x[c].
                model.Add(pair_var <= x[a - 1])
                model.Add(pair_var <= x[c - 1])
                model.Add(pair_var >= x[a - 1] + x[c - 1] - 1)
                # Targeted propagator: pair -> NOT x[m].
                model.AddImplication(pair_var, x[m - 1].Not())
                pair_clauses_added += 1

    if symmetry_break and N >= 2:
        add_reflection_lex_break(model, x)

    total = sum(x)
    if decision_size is None:
        model.Maximize(total)
    else:
        # A set of size >K contains a 3-AP-free subset of size K, so equality
        # is enough for the decision check and is much tighter than >=K.
        model.Add(total == decision_size)

    if branch_order == "natural":
        ordered_vars = x
    elif branch_order in {"degree", "reverse-degree"}:
        degrees = {i: 0 for i in range(1, N + 1)}
        for triple in triples:
            for value in triple:
                degrees[value] += 1
        center = (N + 1) / 2
        ordered_values = sorted(range(1, N + 1), key=lambda value: (-degrees[value], abs(value - center), value))
        if branch_order == "reverse-degree":
            ordered_values.reverse()
        ordered_vars = [x[value - 1] for value in ordered_values]
    else:
        raise ValueError(f"unknown branch_order: {branch_order}")
    value_strategy = cp_model.SELECT_MAX_VALUE if branch_value == "max" else cp_model.SELECT_MIN_VALUE
    model.AddDecisionStrategy(ordered_vars, cp_model.CHOOSE_FIRST, value_strategy)
    if hint:
        for value in hint:
            model.AddHint(x[value - 1], 1)

    solver = cp_model.CpSolver()
    solver.parameters.num_search_workers = workers
    solver.parameters.random_seed = 1194
    solver.parameters.log_search_progress = log
    if fixed_search:
        solver.parameters.search_branching = cp_model.FIXED_SEARCH
    if time_limit is not None:
        solver.parameters.max_time_in_seconds = time_limit

    t0 = time.time()
    status = solver.Solve(model)
    seconds = time.time() - t0

    selected: list[int] = []
    if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        selected = [i + 1 for i, var in enumerate(x) if solver.Value(var)]

    if decision_size is None:
        certifies_optimal = status == cp_model.OPTIMAL
        upper_bound = int(round(solver.BestObjectiveBound()))
    else:
        certifies_optimal = status in (cp_model.OPTIMAL, cp_model.INFEASIBLE)
        upper_bound = decision_size - 1 if status == cp_model.INFEASIBLE else N
    best_size = len(selected)
    verification = verify(selected, N=N) if selected else None
    return {
        "N": N,
        "mode": "optimize" if decision_size is None else "decision",
        "decision_size": decision_size,
        "r_3": best_size if decision_size is None and certifies_optimal else None,
        "best_size": best_size,
        "upper_bound": upper_bound,
        "certifies_optimal": certifies_optimal,
        "solver_status": int(status),
        "solver_status_name": solver.StatusName(status),
        "objective_value": int(round(solver.ObjectiveValue())) if selected and decision_size is None else None,
        "is_feasible_for_decision_size": (
            status in (cp_model.OPTIMAL, cp_model.FEASIBLE) if decision_size is not None else None
        ),
        "ap_constraints": len(triples),
        "window_constraints": window_constraints_added,
        "pair_clauses": pair_clauses_added,
        "branches": solver.NumBranches(),
        "conflicts": solver.NumConflicts(),
        "wall_time": round(solver.WallTime(), 4),
        "seconds": round(seconds, 4),
        "workers": workers,
        "fixed_in": fixed_in,
        "fixed_out": fixed_out,
        "hint_size": len(hint),
        "branch_order": branch_order,
        "branch_value": branch_value,
        "fixed_search": fixed_search,
        "witness": selected,
        "witness_verified": verification["ok"] if verification else False,
        "witness_report": verification,
    }


def add_reflection_lex_break(model: cp_model.CpModel, x: list[cp_model.IntVar]) -> None:
    """Break the reflection symmetry by requiring x lexicographically >= reverse(x)."""
    allowed = [
        (0, 0, 0, 0),
        (0, 0, 1, 0),
        (0, 1, 0, 0),
        (0, 1, 1, 0),
        (1, 0, 0, 1),
        (1, 1, 1, 1),
        (1, 1, 0, 0),
    ]
    prev_equal = model.NewBoolVar("reflection_prefix_equal_0")
    model.Add(prev_equal == 1)
    for offset in range(len(x) // 2):
        left = x[offset]
        right = x[len(x) - 1 - offset]
        next_equal = model.NewBoolVar(f"reflection_prefix_equal_{offset + 1}")
        model.AddAllowedAssignments([prev_equal, left, right, next_equal], allowed)
        prev_equal = next_equal


def compact_result(result: dict, include_witness: bool) -> dict:
    keys = [
        "N",
        "mode",
        "decision_size",
        "r_3",
        "best_size",
        "upper_bound",
        "certifies_optimal",
        "solver_status_name",
        "ap_constraints",
        "branches",
        "conflicts",
        "seconds",
        "witness_verified",
        "fixed_in",
        "fixed_out",
        "hint_size",
        "branch_order",
        "branch_value",
        "fixed_search",
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
    parser.add_argument("--workers", type=int, default=8)
    parser.add_argument("--decision-size", type=int, default=None,
                        help="solve feasibility for a 3-AP-free set of at least this size")
    parser.add_argument("--fix-in", type=Path, default=None,
                        help="JSON list/dict of elements forced into the set")
    parser.add_argument("--fix-out", type=Path, default=None,
                        help="JSON list/dict of elements forced out of the set")
    parser.add_argument("--hint", type=Path, default=None,
                        help="JSON list/dict of a candidate set used as CP-SAT solution hint")
    parser.add_argument("--branch-order", choices=["natural", "degree", "reverse-degree"], default="natural")
    parser.add_argument("--branch-value", choices=["max", "min"], default="max")
    parser.add_argument("--fixed-search", action="store_true",
                        help="ask CP-SAT to use the specified decision strategy as fixed search")
    parser.add_argument("--no-symmetry-break", action="store_true")
    parser.add_argument("--witness", action="store_true")
    parser.add_argument("--oeis", type=Path, default=None)
    parser.add_argument("--window-bounds", type=Path, default=None,
                        help="Path to OEIS A003002 b-file (lines 'n r_3(n)'); "
                             "adds window-cardinality constraints |A∩[a,a+L-1]| ≤ r_3(L).")
    parser.add_argument("--pair-clauses-window", type=str, default=None,
                        help="LO,HI: add targeted pair-AND Tseitin propagators for midpoints "
                             "in [LO,HI].  Redundant with triple constraints but provides "
                             "additional propagation hooks; experimental.")
    parser.add_argument("--output", type=Path, default=None)
    parser.add_argument("--save-full", type=Path, default=None,
                        help="write full solver output, including UNKNOWN runs")
    parser.add_argument("--log", action="store_true")
    args = parser.parse_args()

    oeis = load_oeis(args.oeis) if args.oeis else {}
    fixed_in = load_int_set(args.fix_in) if args.fix_in else []
    fixed_out = load_int_set(args.fix_out) if args.fix_out else []
    hint = load_int_set(args.hint) if args.hint else []
    window_bounds = load_window_bounds(args.window_bounds) if args.window_bounds else {}
    pair_clauses_window: tuple[int, int] | None = None
    if args.pair_clauses_window:
        parts = [p.strip() for p in args.pair_clauses_window.split(",") if p.strip()]
        if len(parts) != 2:
            parser.error("--pair-clauses-window must be LO,HI")
        pair_clauses_window = (int(parts[0]), int(parts[1]))
    Ns = range(args.range[0], args.range[1] + 1) if args.range else [args.N]
    if any(N is None for N in Ns):
        parser.error("specify N or --range START END")

    rows = []
    all_ok = True
    for N in Ns:
        result = solve_r3_cpsat(
            int(N),
            time_limit=args.time_limit,
            workers=args.workers,
            symmetry_break=not args.no_symmetry_break,
            log=args.log,
            decision_size=args.decision_size,
            fixed_in=fixed_in,
            fixed_out=fixed_out,
            hint=hint,
            branch_order=args.branch_order,
            branch_value=args.branch_value,
            fixed_search=args.fixed_search,
            window_bounds=window_bounds,
            pair_clauses_window=pair_clauses_window,
        )
        if int(N) in oeis:
            result["oeis"] = oeis[int(N)]
            result["matches_oeis"] = (
                result["certifies_optimal"]
                and args.decision_size is None
                and result["r_3"] == oeis[int(N)]
            )
            all_ok = all_ok and result["matches_oeis"]
        elif not result["certifies_optimal"]:
            all_ok = False
        rows.append(result)

        compact = compact_result(result, include_witness=args.witness)
        if "oeis" in result:
            compact["oeis"] = result["oeis"]
            compact["matches_oeis"] = result["matches_oeis"]
        print(json.dumps(compact, indent=2), flush=True)

    payload = rows[0] if len(rows) == 1 else {"results": rows}
    for output_path in [args.output, args.save_full]:
        if output_path:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with output_path.open("w", encoding="utf-8") as fh:
                json.dump(payload, fh, indent=2)
                fh.write("\n")

    return 0 if all_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
