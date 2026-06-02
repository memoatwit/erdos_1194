"""
Erdős Problem #42 attack via CP-SAT.

Problem (open, $100):
  If A, B ⊂ [1, N] are Sidon sets with (A - A) ∩ (B - B) = {0}, is
  C(|A|, 2) + C(|B|, 2) ≤ C(f(N), 2) + O(1),
  where f(N) := max |A| over Sidon A ⊂ [1, N]?

Strategy:
  1. Compute f(N) by CP-SAT: max Σ y_i s.t. {y_i} encodes a Sidon set.
  2. Compute g(N) by CP-SAT: max Σ u_{ij} + Σ v_{ij} s.t.
       y_i, z_i ∈ {0, 1}
       u_{ij} = y_i ∧ y_j
       v_{ij} = z_i ∧ z_j
       for each d ∈ [1, N-1]:
         Σ_{j-i=d} u_{ij} + Σ_{j-i=d} v_{ij} ≤ 1
     (This single constraint encodes BOTH the Sidon condition for A
      and B individually AND the disjoint-difference condition.)
  3. Tabulate g(N), C(f(N), 2), and the gap g(N) - C(f(N), 2).

Usage:
  python3 solve_42.py f 20        # compute f(20)
  python3 solve_42.py g 20        # compute g(20)
  python3 solve_42.py sweep 30    # sweep N from 10..30
"""
from __future__ import annotations
import os, sys, json, time, math
from ortools.sat.python import cp_model

THIS_DIR = os.path.dirname(os.path.abspath(__file__))


def solve_f(N: int, time_limit_s: float = 30.0, num_workers: int = 8) -> dict:
    """Compute f(N) = max |A| over Sidon A ⊂ [1, N]."""
    t0 = time.time()
    model = cp_model.CpModel()
    y = [None] + [model.NewBoolVar(f"y_{i}") for i in range(1, N + 1)]

    # u_{i,j} = y_i ∧ y_j for i < j (only needed for Sidon check)
    # Use Sidon constraint: at most one pair per difference d.
    for d in range(1, N):
        pairs = []
        for i in range(1, N - d + 1):
            u = model.NewBoolVar(f"uf_{i}_{i+d}")
            model.AddBoolAnd([y[i], y[i + d]]).OnlyEnforceIf(u)
            model.AddBoolOr([y[i].Not(), y[i + d].Not()]).OnlyEnforceIf(u.Not())
            pairs.append(u)
        model.Add(sum(pairs) <= 1)

    model.Maximize(sum(y[i] for i in range(1, N + 1)))
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = time_limit_s
    solver.parameters.num_search_workers = num_workers
    status = solver.Solve(model)
    elapsed = time.time() - t0
    if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        A = [i for i in range(1, N + 1) if solver.Value(y[i]) == 1]
        return {
            "status": "optimal" if status == cp_model.OPTIMAL else "feasible",
            "N": N, "f": len(A), "A": A,
            "bound": solver.BestObjectiveBound(),
            "time_s": elapsed,
        }
    return {"status": "no_sol", "time_s": elapsed,
            "solver_status": solver.StatusName(status)}


def solve_g(N: int, time_limit_s: float = 60.0, num_workers: int = 8,
            hint_A: list[int] | None = None, hint_B: list[int] | None = None,
            symmetry_break: bool = True) -> dict:
    """Compute g(N) = max C(|A|,2) + C(|B|,2) over disjoint-difference Sidon
    pairs (A, B) ⊂ [1, N]."""
    t0 = time.time()
    model = cp_model.CpModel()
    y = [None] + [model.NewBoolVar(f"y_{i}") for i in range(1, N + 1)]
    z = [None] + [model.NewBoolVar(f"z_{i}") for i in range(1, N + 1)]

    pair_sum = []
    a_pairs = []   # for |A| count via pair lookup
    b_pairs = []
    for d in range(1, N):
        # u_{i,i+d} = y_i ∧ y_{i+d}, v_{i,i+d} = z_i ∧ z_{i+d}
        d_terms = []
        for i in range(1, N - d + 1):
            u = model.NewBoolVar(f"u_{i}_{i+d}")
            model.AddBoolAnd([y[i], y[i + d]]).OnlyEnforceIf(u)
            model.AddBoolOr([y[i].Not(), y[i + d].Not()]).OnlyEnforceIf(u.Not())
            v = model.NewBoolVar(f"v_{i}_{i+d}")
            model.AddBoolAnd([z[i], z[i + d]]).OnlyEnforceIf(v)
            model.AddBoolOr([z[i].Not(), z[i + d].Not()]).OnlyEnforceIf(v.Not())
            d_terms.append(u)
            d_terms.append(v)
            a_pairs.append(u)
            b_pairs.append(v)
        # Disjoint-difference + Sidon-for-each: ≤ 1 pair (across A AND B)
        model.Add(sum(d_terms) <= 1)
        pair_sum.extend(d_terms)

    # Symmetry breaking: WLOG sum_{i} y_i ≥ sum_{i} z_i (i.e., |A| ≥ |B|)
    # Plus: WLOG first element of A is at most as far from N as last
    # element (left-bias). This reduces (A → reverse) and (A ↔ B) symmetries.
    if symmetry_break:
        # |A| >= |B|: encode as sum y_i >= sum z_i.
        sum_y = sum(y[i] for i in range(1, N + 1))
        sum_z = sum(z[i] for i in range(1, N + 1))
        model.Add(sum_y >= sum_z)

    model.Maximize(sum(pair_sum))

    if hint_A is not None:
        seen = set(hint_A)
        for i in range(1, N + 1):
            model.AddHint(y[i], 1 if i in seen else 0)
    if hint_B is not None:
        seen = set(hint_B)
        for i in range(1, N + 1):
            model.AddHint(z[i], 1 if i in seen else 0)

    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = time_limit_s
    solver.parameters.num_search_workers = num_workers
    status = solver.Solve(model)
    elapsed = time.time() - t0
    if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        A = [i for i in range(1, N + 1) if solver.Value(y[i]) == 1]
        B = [i for i in range(1, N + 1) if solver.Value(z[i]) == 1]
        obj = int(solver.ObjectiveValue())
        return {
            "status": "optimal" if status == cp_model.OPTIMAL else "feasible",
            "N": N, "g": obj,
            "C(|A|,2)": len(A) * (len(A) - 1) // 2,
            "C(|B|,2)": len(B) * (len(B) - 1) // 2,
            "|A|": len(A), "|B|": len(B), "A": A, "B": B,
            "bound": solver.BestObjectiveBound(),
            "time_s": elapsed,
        }
    return {"status": "no_sol", "time_s": elapsed,
            "solver_status": solver.StatusName(status)}


def sweep(N_max: int = 30, time_per: float = 30.0, num_workers: int = 8,
          save_path: str | None = None) -> list[dict]:
    """Compute f(N) and g(N) for N in a range, tabulate."""
    rows = []
    if save_path and os.path.exists(save_path):
        try:
            rows = json.load(open(save_path))
            print(f"Resumed: {len(rows)} prior rows", flush=True)
        except Exception:
            rows = []
    done_N = {r["N"] for r in rows}
    for N in range(2, N_max + 1):
        if N in done_N:
            continue
        print(f"\n=== N = {N} ===", flush=True)
        fr = solve_f(N, time_limit_s=time_per, num_workers=num_workers)
        print(f"  f({N}) = {fr.get('f')}  A = {fr.get('A')}  t={fr['time_s']:.1f}s")
        gr = solve_g(N, time_limit_s=time_per * 2, num_workers=num_workers,
                     hint_A=fr.get("A"))
        if gr.get("g") is None:
            print(f"  g({N}) FAILED ({gr['status']})")
            row = {"N": N, **fr, "g_row": gr}
        else:
            f = fr["f"]
            g = gr["g"]
            cf2 = f * (f - 1) // 2
            gap = g - cf2
            print(f"  g({N}) = {g}  C(f({N}),2) = {cf2}  gap = {gap:+d}  "
                  f"|A|={gr['|A|']} |B|={gr['|B|']}")
            row = {
                "N": N, "f(N)": f, "C(f(N),2)": cf2, "g(N)": g, "gap": gap,
                "|A|": gr["|A|"], "|B|": gr["|B|"], "A": gr["A"], "B": gr["B"],
                "A_opt": fr["A"],
                "time_f_s": fr["time_s"], "time_g_s": gr["time_s"],
            }
        rows.append(row)
        if save_path:
            with open(save_path, "w") as f:
                json.dump(rows, f, indent=2, default=str)
    return rows


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    mode = sys.argv[1]
    if mode == "f":
        N = int(sys.argv[2])
        print(json.dumps(solve_f(N, time_limit_s=30), indent=2, default=str))
    elif mode == "g":
        N = int(sys.argv[2])
        print(json.dumps(solve_g(N, time_limit_s=60), indent=2, default=str))
    elif mode == "sweep":
        N_max = int(sys.argv[2])
        out = os.path.join(THIS_DIR, f"sweep_{N_max}.json")
        rows = sweep(N_max=N_max, time_per=15.0, save_path=out)
        print(f"\nSaved → {out}")
        print(f"\n{'N':>3} {'f(N)':>5} {'C(f,2)':>7} {'g(N)':>5} {'gap':>5} "
              f"{'|A|':>3} {'|B|':>3}")
        for r in rows:
            if "gap" in r:
                print(f"{r['N']:>3} {r['f(N)']:>5} {r['C(f(N),2)']:>7} "
                      f"{r['g(N)']:>5} {r['gap']:>+5} {r['|A|']:>3} {r['|B|']:>3}")
    else:
        print(f"Unknown mode: {mode}")
