"""
Phase 4 — exact search using Google ortools CP-SAT.

Find smallest M such that there is a Sidon A subset [1, M] with {1, M} <= A
and [1, N] subset (A - A).  For each candidate M, solve a feasibility CSP.

CSP variables:
  y_i in {0, 1}  for i in [1, M]    -- y_i = 1 iff i in A
  z_{i,j} in {0,1}  for 1 <= i < j <= M, j - i <= max(N, M-1)
                                       -- z = y_i AND y_j

Constraints:
  y_1 = 1, y_M = 1                   -- anchor
  z_{i,j} = AND(y_i, y_j)            -- via z <= y_i, z <= y_j, z >= y_i+y_j-1
  for d in [1, M-1]:
    sum_{j - i = d} z_{i,j} <= 1     -- Sidon
  for n in [1, N]:
    sum_{j - i = n} z_{i,j} >= 1     -- coverage

Search strategy: scan M = M_lo, ..., upward; first feasible M is optimum.
Use CP-SAT's parallel search.

Usage:
  python3 exact_search_cpsat.py 20 30 50
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


def feasible_at_M(N: int, M: int, time_limit_s: float = 60.0,
                  num_workers: int = 8) -> tuple[list[int] | None, dict]:
    """Solve PDS feasibility at fixed M with CP-SAT."""
    t0 = time.time()
    model = cp_model.CpModel()

    y = [None] + [model.NewBoolVar(f"y_{i}") for i in range(1, M + 1)]
    model.Add(y[1] == 1)
    model.Add(y[M] == 1)

    # z[i][j] for i < j: j - i in [1, M-1].  We only need diffs up to M-1.
    # To keep model small, only construct z when we need it (every d).
    # Sidon and coverage constraints both group by d = j - i.
    for d in range(1, M):
        # All pairs with diff d.
        pairs = [(i, i + d) for i in range(1, M - d + 1)]
        z_pairs = []
        for (i, j) in pairs:
            zij = model.NewBoolVar(f"z_{i}_{j}")
            model.AddBoolAnd([y[i], y[j]]).OnlyEnforceIf(zij)
            model.AddBoolOr([y[i].Not(), y[j].Not()]).OnlyEnforceIf(zij.Not())
            z_pairs.append(zij)
        # Sidon: at most one of z_pairs is true
        model.Add(sum(z_pairs) <= 1)
        # Coverage: if d in [1, N], at least one z_pair is true
        if d <= N:
            model.Add(sum(z_pairs) >= 1)

    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = time_limit_s
    solver.parameters.num_search_workers = num_workers
    status = solver.Solve(model)
    elapsed = time.time() - t0

    if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        A = [i for i in range(1, M + 1) if solver.Value(y[i]) == 1]
        return A, {"status": "feasible", "time_s": elapsed,
                   "solver_status": solver.StatusName(status)}
    elif status == cp_model.INFEASIBLE:
        return None, {"status": "infeasible", "time_s": elapsed,
                      "solver_status": "INFEASIBLE"}
    else:
        return None, {"status": "timeout", "time_s": elapsed,
                      "solver_status": solver.StatusName(status)}


def solve_exact_cpsat(N: int, M_hi: int | None = None,
                      time_limit_per_M: float = 30.0,
                      total_budget_s: float = 300.0,
                      num_workers: int = 8,
                      resume: bool = True) -> dict:
    """Scan M upward, first feasible is optimum."""
    M_lo = lower_bound_M(N)
    if M_hi is None:
        M_hi = 100 * N

    save_path = os.path.join(RESULTS, f"exact_cpsat_N{N}.json")
    log = []
    if resume and os.path.exists(save_path):
        try:
            prev = json.load(open(save_path))
            if prev.get("status") == "solved":
                print(f"[N={N}] already solved at M = {prev['M_opt']}")
                return prev
            log = prev.get("log", [])
            last_tested = max((e["M"] for e in log), default=M_lo - 1)
            M_lo = last_tested + 1
        except Exception:
            pass

    print(f"[N={N}] CP-SAT scan starting at M = {M_lo}")

    t_global = time.time()
    deadline = t_global + total_budget_s
    for M in range(M_lo, M_hi + 1):
        if time.time() > deadline:
            partial = {"N": N, "status": "global_timeout", "log": log}
            with open(save_path, "w") as f:
                json.dump(partial, f, indent=2, default=str)
            return partial
        budget = min(time_limit_per_M, deadline - time.time())
        print(f"  M = {M:5d} ...", end="", flush=True)
        A, stats = feasible_at_M(N, M, time_limit_s=budget,
                                  num_workers=num_workers)
        log.append({"M": M, **stats, "A_len": (len(A) if A else None)})
        print(f"  {stats['status']:>11s}  t={stats['time_s']:.2f}s"
              + (f"  |A|={len(A)}" if A else ""))
        with open(save_path, "w") as f:
            json.dump({"N": N, "status": "in_progress", "log": log}, f,
                      indent=2, default=str)
        if A is not None:
            result = {
                "N": N, "M_opt": M, "A_opt": A, "log": log,
                "total_time_s": time.time() - t_global,
                "status": "solved",
            }
            with open(save_path, "w") as f:
                json.dump(result, f, indent=2, default=str)
            return result
        if stats["status"] == "timeout":
            partial = {"N": N, "M_so_far": M, "status": "timeout", "log": log}
            with open(save_path, "w") as f:
                json.dump(partial, f, indent=2, default=str)
            return partial
    return {"N": N, "status": "exhausted", "log": log}


if __name__ == "__main__":
    args = [int(a) for a in sys.argv[1:]] or [20]
    os.makedirs(RESULTS, exist_ok=True)
    for N in args:
        print("=" * 70)
        print(f" PHASE 4 CP-SAT EXACT SEARCH for N = {N}")
        print("=" * 70)
        result = solve_exact_cpsat(N, time_limit_per_M=30.0,
                                    total_budget_s=300.0,
                                    num_workers=8, resume=True)
        print()
        print(f"  RESULT for N={N}: {result.get('status')}")
        if result.get("M_opt"):
            print(f"  Optimal max(A) = {result['M_opt']}")
            print(f"  Optimal A      = {result['A_opt']}")
            print(f"  |A_opt|        = {len(result['A_opt'])}")
