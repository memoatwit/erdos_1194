"""
Phase 4 — single-solve CP-SAT optimization for PDS minimizing max(A).

Same CSP as exact_search_cpsat.py, but instead of scanning M upward, we
fix a generous M_max upper bound and let CP-SAT minimize max(A) in one
solve, using incumbent pruning.

Variables:
  y_i in {0,1} for i in [1, M_max]
  z_{i,j} in {0,1} for i < j with j-i in [1, M_max-1]
  m in [N+1, M_max]                         -- the value max(A)

Constraints:
  y_1 = 1
  y_i = 1 implies i <= m   (i.e., m >= i for any selected i)
  for i in [1, M_max]: i*y_i <= m   (linear constraint)
  ... and m must be selected: y_m = 1  (we drop this so that only the
       relevant max is selected)
  Sidon: sum_{j-i=d} z <= 1 for each d
  Coverage: sum_{j-i=n} z >= 1 for n in [1, N]
  z = AND(y_i, y_j)

Objective: minimize m.
"""
from __future__ import annotations
import sys
import os
import json
import time
import math

from ortools.sat.python import cp_model

THIS_DIR = os.path.dirname(os.path.abspath(__file__))
RESULTS  = os.path.join(THIS_DIR, "results")


def lower_bound_M(N: int) -> int:
    K_min  = math.ceil((1 + math.sqrt(1 + 8 * N)) / 2)
    return max(N + 1, 1 + K_min * (K_min - 1) // 2)


def optimize_max(N: int, M_max: int, time_limit_s: float = 60.0,
                 num_workers: int = 8,
                 hint_A: list[int] | None = None) -> dict:
    """Single-solve CP-SAT minimizing max(A)."""
    t0 = time.time()
    model = cp_model.CpModel()

    y = [None] + [model.NewBoolVar(f"y_{i}") for i in range(1, M_max + 1)]
    model.Add(y[1] == 1)

    # m = max(i: y_i = 1).  Use linear: i * y_i <= m for each i.
    M_lo = lower_bound_M(N)
    m = model.NewIntVar(M_lo, M_max, "m")
    for i in range(1, M_max + 1):
        # If y_i is true, m must be >= i.  Easy linearization:
        #   m >= i * y_i  (works because y is 0/1)
        model.Add(m >= i * y[i])
    # And we need at least one y_i true with i = m: not strictly needed if
    # we minimize m (the optimum will achieve equality).

    # z and Sidon/coverage
    for d in range(1, M_max):
        pairs = [(i, i + d) for i in range(1, M_max - d + 1)]
        z_pairs = []
        for (i, j) in pairs:
            zij = model.NewBoolVar(f"z_{i}_{j}")
            model.AddBoolAnd([y[i], y[j]]).OnlyEnforceIf(zij)
            model.AddBoolOr([y[i].Not(), y[j].Not()]).OnlyEnforceIf(zij.Not())
            z_pairs.append(zij)
        model.Add(sum(z_pairs) <= 1)
        if d <= N:
            model.Add(sum(z_pairs) >= 1)

    # Hint from greedy: speeds finding initial incumbent.
    if hint_A:
        hint_A_set = set(hint_A)
        for i in range(1, M_max + 1):
            model.AddHint(y[i], 1 if i in hint_A_set else 0)
        model.AddHint(m, max(hint_A))

    model.Minimize(m)

    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = time_limit_s
    solver.parameters.num_search_workers = num_workers
    solver.parameters.log_search_progress = False
    status = solver.Solve(model)
    elapsed = time.time() - t0

    if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        A = [i for i in range(1, M_max + 1) if solver.Value(y[i]) == 1]
        return {
            "status": "solved" if status == cp_model.OPTIMAL else "feasible_only",
            "M_opt": int(solver.Value(m)),
            "A_opt": A,
            "time_s": elapsed,
            "best_bound": solver.BestObjectiveBound(),
            "solver_status": solver.StatusName(status),
        }
    return {"status": "no_solution", "time_s": elapsed,
            "solver_status": solver.StatusName(status)}


if __name__ == "__main__":
    args = [int(a) for a in sys.argv[1:]] or [20]
    os.makedirs(RESULTS, exist_ok=True)
    for N in args:
        print("=" * 70)
        print(f" PHASE 4 CP-SAT OPTIMIZATION for N = {N}")
        print("=" * 70)
        # Use greedy as upper bound and hint
        from exact_search import lower_bound_M as _lb
        # Generous M_max: 2x lower bound or known greedy, whichever lower
        from explore import build
        try:
            A_g, _, _ = build(N, verbose=False)
            M_greedy = max(A_g)
            print(f"  greedy hint: max(A)={M_greedy}, |A|={len(A_g)}")
            M_max_use = min(M_greedy, max(N + 1, 4 * _lb(N)))
        except Exception as e:
            print(f"  greedy unavailable: {e}")
            A_g = None
            M_max_use = 4 * _lb(N)

        print(f"  M_max for model: {M_max_use}")
        print(f"  solving ...")
        result = optimize_max(N, M_max_use, time_limit_s=120.0,
                              num_workers=8, hint_A=A_g)
        result["N"] = N
        print()
        print(f"  RESULT for N={N}: {result['status']}")
        if result.get("M_opt"):
            print(f"  Best max(A) found = {result['M_opt']}")
            print(f"  Best bound        = {result['best_bound']}")
            print(f"  A                 = {result['A_opt']}")
            print(f"  |A|               = {len(result['A_opt'])}")
            print(f"  Time              = {result['time_s']:.2f}s")
        out = os.path.join(RESULTS, f"exact_cpsat_opt_N{N}.json")
        with open(out, "w") as f:
            json.dump(result, f, indent=2, default=str)
        print(f"  Saved → {out}")
