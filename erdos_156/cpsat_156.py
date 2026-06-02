"""
CP-SAT model for Erdős Problem #156.

Given N and k, decide whether there is a Sidon set A ⊂ [1, N] with |A| = k
that is *maximal* (no element of [1, N] \\ A can be added while preserving
Sidon).

Variables:
  y_i ∈ {0, 1}  for i ∈ [1, N]                 indicator i ∈ A
  u_{i,j} ∈ {0, 1}  for 1 ≤ i < j ≤ N          u = y_i ∧ y_j (pair indicator)

Constraints:
  Cardinality:  Σ y_i = k.
  Sidon:        Σ_{j - i = d} u_{i,j} ≤ 1     for each d ∈ [1, N-1].

  Symmetry break: y_1 + y_N ≥ 1 (translate so left or right boundary is hit)?
    actually break by enforcing  Σ_{i ≤ (N+1)/2} y_i ≥ Σ_{i > (N+1)/2} y_i

  Maximality: for every x ∈ [1, N], at least one of:
     - y_x = 1
     - (existing-diff blocker) ∃ distinct a₁, a₂, a₃ ∈ A with
       y_{a₁} = y_{a₂} = y_{a₃} = 1 and a₃ - a₁ = |x - a₂|.
     - (symmetric blocker) ∃ distinct a₁, a₂ ∈ A with a₁ + a₂ = 2x.

  We encode each blocker case as an auxiliary Boolean and OR them via
  AddBoolOr with the OnlyEnforceIf(y_x.Not()) pattern.

Usage:
  python3 cpsat_156.py N k [time_limit_s]
"""
from __future__ import annotations
import sys, time, json
from ortools.sat.python import cp_model


def solve_156_cpsat(N: int, k: int, time_limit_s: float = 60.0,
                    num_workers: int = 8) -> dict:
    t0 = time.time()
    model = cp_model.CpModel()
    y = [None] + [model.NewBoolVar(f"y_{i}") for i in range(1, N + 1)]

    # Sidon via pair Booleans
    u = {}
    for d in range(1, N):
        d_pairs = []
        for i in range(1, N - d + 1):
            j = i + d
            uij = model.NewBoolVar(f"u_{i}_{j}")
            model.AddBoolAnd([y[i], y[j]]).OnlyEnforceIf(uij)
            model.AddBoolOr([y[i].Not(), y[j].Not()]).OnlyEnforceIf(uij.Not())
            u[(i, j)] = uij
            d_pairs.append(uij)
        model.Add(sum(d_pairs) <= 1)

    # Cardinality
    model.Add(sum(y[i] for i in range(1, N + 1)) == k)

    # Symmetry break: prefer y_1 = 1 (translate so first element is 1).
    # WARNING: this assumes m(N) attains a witness containing 1. The known
    # data is mixed — sometimes a_1 is small, sometimes not. So we DON'T
    # enforce y_1 = 1. Instead break by: more elements in left half than right.
    left = sum(y[i] for i in range(1, (N + 1) // 2 + 1))
    right = sum(y[i] for i in range((N + 1) // 2 + 1, N + 1))
    model.Add(left >= right)

    # Maximality: for each x ∉ A, blocker fires.
    # We model: for each x, define blocker[x] = OR of all blocker events.
    # Then add: y_x ∨ blocker[x].

    for x in range(1, N + 1):
        # Collect blocker indicator variables for x.
        blockers = []

        # Type 2 (symmetric): pair (a1, a2) with a1 + a2 = 2x.
        # a1 < a2, a1 + a2 = 2x, so a1 < x < a2, a1 + a2 = 2x.
        # I.e., a1 = x - t, a2 = x + t for t in [1, min(x-1, N-x)].
        for t in range(1, min(x, N - x + 1)):
            a1 = x - t
            a2 = x + t
            if a1 < 1 or a2 > N:
                continue
            # Blocker fires iff y_{a1} = y_{a2} = 1.
            # Use u_{a1, a2} (if exists). The pair has diff 2t.
            if (a1, a2) in u:
                blockers.append(u[(a1, a2)])

        # Type 1 (existing-diff): triple (a1, a2, a3) distinct in A with
        # a3 - a1 = |x - a2|.
        # Enumerate over choice of a3 - a1 = d and a2 with |x - a2| = d.
        # I.e., for each d ≥ 1, for each pair (a1, a3) with a3 - a1 = d,
        # for each a2 ∈ {x - d, x + d} (if in [1, N] and a2 ≠ a1, a3):
        for d in range(1, N):
            # Pairs (a1, a3) with a3 - a1 = d, both in [1, N], are
            # (i, i+d) for i in [1, N-d].
            for a2 in (x - d, x + d):
                if a2 < 1 or a2 > N:
                    continue
                # For each pair (a1, a3) with a3 - a1 = d, a2 ≠ a1, a2 ≠ a3,
                # the blocker fires when y_{a1} = y_{a2} = y_{a3} = 1.
                for i in range(1, N - d + 1):
                    a1, a3 = i, i + d
                    if a2 == a1 or a2 == a3:
                        continue
                    # Introduce blocker variable.
                    # blk = u_{a1, a3} ∧ y_{a2}
                    blk = model.NewBoolVar(f"blk_x{x}_t1_d{d}_a2_{a2}_p{a1}_{a3}")
                    model.AddBoolAnd([u[(a1, a3)], y[a2]]).OnlyEnforceIf(blk)
                    model.AddBoolOr([u[(a1, a3)].Not(), y[a2].Not()]).OnlyEnforceIf(blk.Not())
                    blockers.append(blk)

        # Maximality: y_x OR (any blocker).
        if blockers:
            model.AddBoolOr([y[x]] + blockers)
        else:
            # No blocker possible → forced y_x = 1.
            model.Add(y[x] == 1)

    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = time_limit_s
    solver.parameters.num_search_workers = num_workers
    status = solver.Solve(model)
    elapsed = time.time() - t0

    if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
        A = [i for i in range(1, N + 1) if solver.Value(y[i]) == 1]
        return {"N": N, "k": k, "status": "feasible", "A": A,
                "time_s": elapsed, "solver_status": solver.StatusName(status)}
    if status == cp_model.INFEASIBLE:
        return {"N": N, "k": k, "status": "infeasible", "time_s": elapsed,
                "solver_status": solver.StatusName(status)}
    return {"N": N, "k": k, "status": "timeout", "time_s": elapsed,
            "solver_status": solver.StatusName(status)}


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(1)
    N = int(sys.argv[1])
    k = int(sys.argv[2])
    tlim = float(sys.argv[3]) if len(sys.argv) >= 4 else 60.0
    r = solve_156_cpsat(N, k, time_limit_s=tlim)
    print(json.dumps(r, indent=2))
