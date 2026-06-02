"""
Phase 4' — Extension cost from finite optima.

Given a known finite optimum A_N* (a Sidon A subset [1, M*(N)] covering
[1, N] as differences), measure the minimum max(A) over A' >= A_N* that
is Sidon and covers [1, N+k] for k = 1, 2, 3, ...

Comparing M_ext(N, k) to the unconstrained optimum M*(N+k) measures the
"extension obstruction" — how much we pay for being forced to extend a
previous optimum rather than starting fresh.

Implementation: same CP-SAT model as exact_search_cpsat_opt.py, with
y_i = 1 forced for i in A_N*.

Usage:
  python3 extension_cost.py
"""
from __future__ import annotations
import os, json, time, math, sys
from ortools.sat.python import cp_model

THIS_DIR = os.path.dirname(os.path.abspath(__file__))
RESULTS  = os.path.join(THIS_DIR, "results")


# Known finite optima from Phase 4
KNOWN_OPTIMA = {
    20: {"M_opt": 36, "A_opt": [1, 5, 6, 18, 20, 26, 29, 36]},
    25: {"M_opt": 46, "A_opt": [1, 3, 11, 25, 26, 30, 37, 43, 46]},
    30: {"M_opt": 56, "A_opt": [1, 2, 7, 11, 24, 27, 35, 42, 54, 56]},
    35: {"M_opt": 56, "A_opt": [1, 2, 7, 11, 24, 27, 35, 42, 54, 56]},
    40: {"M_opt": 86, "A_opt": [1, 10, 11, 18, 31, 43, 46, 57, 62, 80, 84, 86]},
    45: {"M_opt": 86, "A_opt": [1, 10, 11, 18, 31, 43, 46, 57, 62, 80, 84, 86]},
}


def covered_prefix(A: list[int]) -> int:
    """Return largest T such that [1, T] subset (A - A)."""
    diffs = set()
    for j in range(len(A)):
        for i in range(j):
            diffs.add(A[j] - A[i])
    T = 0
    while T + 1 in diffs:
        T += 1
    return T


def covers_range(A: list[int], N: int) -> bool:
    """True iff [1, N] subset (A - A)."""
    diffs = set()
    for j in range(len(A)):
        for i in range(j):
            diffs.add(A[j] - A[i])
    return all(n in diffs for n in range(1, N + 1))


def min_extension(A_seed: list[int], N_target: int,
                  M_max: int,
                  time_limit_s: float = 30.0,
                  num_workers: int = 8) -> dict:
    """Minimise max(A) over A subset [1, M_max] with A seed <= A,
    A Sidon, [1, N_target] subset A - A.
    """
    t0 = time.time()
    model = cp_model.CpModel()

    seed_set = set(A_seed)
    y = [None] + [model.NewBoolVar(f"y_{i}") for i in range(1, M_max + 1)]
    for i in seed_set:
        model.Add(y[i] == 1)

    # m = max(i: y_i = 1)
    M_lo = max(A_seed)        # at least the existing max
    m = model.NewIntVar(M_lo, M_max, "m")
    for i in range(1, M_max + 1):
        model.Add(m >= i * y[i])

    for d in range(1, M_max):
        pairs = [(i, i + d) for i in range(1, M_max - d + 1)]
        z_pairs = []
        for (i, j) in pairs:
            zij = model.NewBoolVar(f"z_{i}_{j}")
            model.AddBoolAnd([y[i], y[j]]).OnlyEnforceIf(zij)
            model.AddBoolOr([y[i].Not(), y[j].Not()]).OnlyEnforceIf(zij.Not())
            z_pairs.append(zij)
        model.Add(sum(z_pairs) <= 1)
        if d <= N_target:
            model.Add(sum(z_pairs) >= 1)

    # Hint: keep seed selected, set m to seed max
    for i in range(1, M_max + 1):
        model.AddHint(y[i], 1 if i in seed_set else 0)
    model.AddHint(m, max(A_seed))

    model.Minimize(m)
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = time_limit_s
    solver.parameters.num_search_workers = num_workers
    status = solver.Solve(model)
    elapsed = time.time() - t0

    if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        A = [i for i in range(1, M_max + 1) if solver.Value(y[i]) == 1]
        return {
            "status": "optimal" if status == cp_model.OPTIMAL else "feasible_only",
            "M_ext": int(solver.Value(m)),
            "A_ext": A,
            "best_bound": solver.BestObjectiveBound(),
            "time_s": elapsed,
            "solver_status": solver.StatusName(status),
        }
    return {
        "status": "no_solution",
        "time_s": elapsed,
        "solver_status": solver.StatusName(status),
    }


def trajectory_from_seed(N_seed: int, k_max: int = 5,
                         M_max_per_call: int = 200,
                         time_limit_per_call: float = 25.0,
                         save_path: str | None = None) -> list[dict]:
    """Extend A_{N_seed}^* one step at a time and record M_ext.

    Saves incrementally to save_path after each step (resume-friendly).
    """
    seed_info = KNOWN_OPTIMA[N_seed]
    A_seed = list(seed_info["A_opt"])
    print(f"\n=== Extending A_{N_seed}* (max={max(A_seed)}, |A|={len(A_seed)}) ===",
          flush=True)
    T_covered = covered_prefix(A_seed)
    print(f"  Free coverage of seed: [1, {T_covered}]", flush=True)

    rows = []
    # Resume support
    if save_path and os.path.exists(save_path):
        try:
            rows = json.load(open(save_path))
            print(f"  RESUMED with {len(rows)} prior steps", flush=True)
        except Exception:
            rows = []

    # Determine where to start from
    if rows and rows[-1].get("M_ext") is not None and rows[-1].get("A_ext"):
        current_seed = list(rows[-1]["A_ext"])
        start_step  = (rows[-1]["N"] - N_seed) + 1
    else:
        current_seed = list(A_seed)
        start_step  = 0

    for step in range(start_step, k_max + 1):
        target = N_seed + step
        # If already covered for free, M_ext = current max
        if covers_range(current_seed, target):
            row = {
                "N": target, "M_ext": max(current_seed),
                "A_ext": list(current_seed), "from_free_cov": True,
                "time_s": 0.0,
            }
            rows.append(row)
            print(f"  N={target:3d}  M_ext={row['M_ext']:4d}  (free, no new element)",
                  flush=True)
            if save_path:
                with open(save_path, "w") as f:
                    json.dump(rows, f, indent=2, default=str)
            continue
        # Else: solve for min extension. Start with a small M_max and double
        # if INFEASIBLE.
        cur_max = max(current_seed)
        M_try = max(M_max_per_call, int(2 * cur_max))
        result = None
        for _attempt in range(4):
            result = min_extension(current_seed, target, M_max=M_try,
                                   time_limit_s=time_limit_per_call)
            if result.get("M_ext") is not None:
                break
            if result.get("solver_status") == "INFEASIBLE":
                M_try *= 2
                print(f"    (M_max={M_try//2} infeasible; doubling to {M_try})",
                      flush=True)
                continue
            break  # UNKNOWN/timeout: stop trying
        if result.get("M_ext") is None:
            print(f"  N={target:3d}  FAILED ({result.get('status')}) "
                  f"t={result.get('time_s', 0):.1f}s",
                  flush=True)
            rows.append({"N": target, **result})
            if save_path:
                with open(save_path, "w") as f:
                    json.dump(rows, f, indent=2, default=str)
            break
        row = {
            "N": target, "M_ext": result["M_ext"], "A_ext": result["A_ext"],
            "from_free_cov": False, "time_s": result["time_s"],
            "status": result["status"],
        }
        rows.append(row)
        # Compare to known optimum if available
        opt_known = KNOWN_OPTIMA.get(target, {}).get("M_opt")
        cmp = (f"  vs M*({target})={opt_known}, gap=+{row['M_ext']-opt_known}"
               if opt_known else "")
        print(f"  N={target:3d}  M_ext={row['M_ext']:5d}  |A|={len(row['A_ext'])}  "
              f"t={row['time_s']:.1f}s{cmp}",
              flush=True)
        if save_path:
            with open(save_path, "w") as f:
                json.dump(rows, f, indent=2, default=str)
        # Use new extended set as the seed for next step
        current_seed = list(row["A_ext"])

    return rows


if __name__ == "__main__":
    args = sys.argv[1:]
    if args and args[0] == "long":
        N_seed = int(args[1]) if len(args) > 1 else 30
        k_max  = int(args[2]) if len(args) > 2 else 30
        out = os.path.join(RESULTS, f"extension_long_N{N_seed}.json")
        traj = trajectory_from_seed(N_seed, k_max=k_max,
                                    M_max_per_call=600,
                                    time_limit_per_call=15.0,
                                    save_path=out)
        print(f"\nSaved → {out}")
    else:
        seeds_arg = [int(a) for a in args] or [20, 30, 40]
        all_results = {}
        for N_seed in seeds_arg:
            if N_seed not in KNOWN_OPTIMA:
                print(f"No known optimum for N={N_seed}, skipping")
                continue
            traj = trajectory_from_seed(N_seed, k_max=10,
                                        M_max_per_call=300,
                                        time_limit_per_call=20.0)
            all_results[N_seed] = traj
        out = os.path.join(RESULTS, "extension_cost.json")
        with open(out, "w") as f:
            json.dump(all_results, f, indent=2, default=str)
        print(f"\nSaved → {out}")
