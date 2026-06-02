"""
Erdős Problem #40: B_3 sets.

A set A is a *B_3 set* if every triple sum a+b+c (a, b, c ∈ A) is
uniquely determined by the unordered multiset {a, b, c}. Equivalently,
the multiset of triple sums has no non-trivial coincidences.

Equivalent formulation: the representation function
    r_3(n) := #{(a, b, c) ∈ A^3 : a ≤ b ≤ c, a + b + c = n}
satisfies r_3(n) ≤ 1 for every n.

Tools:
  - is_b3(A): verify
  - f3_greedy(N): Mian-Chowla-analog greedy B_3 set up to max ≤ N
  - f3_exact(N): max |A| over B_3 A ⊂ [1, N] via CP-SAT
"""
from __future__ import annotations
import itertools
import sys
import time


def is_b3(A) -> bool:
    """True iff A is a B_3 set: all sums of three elements (a, b, c)
    with a ≤ b ≤ c are distinct."""
    vals = sorted(set(A))
    seen = {}
    for c_idx in range(len(vals)):
        c = vals[c_idx]
        for b_idx in range(c_idx + 1):
            b = vals[b_idx]
            for a_idx in range(b_idx + 1):
                a = vals[a_idx]
                s = a + b + c
                if s in seen:
                    return False
                seen[s] = (a, b, c)
    return True


def triple_sums(A) -> set:
    vals = sorted(set(A))
    return {vals[i] + vals[j] + vals[k]
            for i in range(len(vals))
            for j in range(i, len(vals))
            for k in range(j, len(vals))}


def b3_greedy(N: int) -> list:
    """Greedy B_3 set: 1, then smallest x ≤ N such that A ∪ {x} is B_3."""
    A = [1]
    sums = {3}   # 1 + 1 + 1
    for x in range(2, N + 1):
        # new triple sums when adding x:
        # (x, x, x); (x, x, a) for a in A; (x, a, b) for a ≤ b in A
        new_sums = set()
        new_sums.add(3 * x)
        ok = True
        for a in A:
            s1 = 2 * x + a   # x + x + a (with x ≥ a since a in A so a ≤ x)
            s2 = x + 2 * a   # x + a + a
            if s1 in sums or s1 in new_sums:
                ok = False; break
            new_sums.add(s1)
            if s2 in sums or s2 in new_sums:
                ok = False; break
            new_sums.add(s2)
        if ok:
            for i, a in enumerate(A):
                for b in A[i + 1:]:
                    s = x + a + b
                    if s in sums or s in new_sums:
                        ok = False; break
                    new_sums.add(s)
                if not ok: break
        if ok:
            A.append(x)
            sums |= new_sums
    return A


def f3_exact_cpsat(N: int, time_limit_s: float = 60.0,
                   num_workers: int = 8) -> dict:
    """Max |A| over B_3 sets A ⊂ [1, N] via CP-SAT."""
    from ortools.sat.python import cp_model
    t0 = time.time()
    model = cp_model.CpModel()
    y = [None] + [model.NewBoolVar(f"y_{i}") for i in range(1, N + 1)]

    # For each possible sum s in [3, 3N], the number of triples (a, b, c)
    # with a ≤ b ≤ c, a + b + c = s, all in A must be ≤ 1.
    triples_by_sum: dict[int, list[tuple[int, int, int]]] = {}
    for a in range(1, N + 1):
        for b in range(a, N + 1):
            for c in range(b, N + 1):
                s = a + b + c
                triples_by_sum.setdefault(s, []).append((a, b, c))

    for s, triples in triples_by_sum.items():
        if len(triples) <= 1:
            continue
        # Indicator z_t = y_a ∧ y_b ∧ y_c
        z_vars = []
        for (a, b, c) in triples:
            z = model.NewBoolVar(f"z_{a}_{b}_{c}")
            # For a, b, c distinct: z = y_a ∧ y_b ∧ y_c
            # For a = b: z = y_a ∧ y_c (etc.)
            members = [y[v] for v in {a, b, c}]
            model.AddBoolAnd(members).OnlyEnforceIf(z)
            model.AddBoolOr([v.Not() for v in members]).OnlyEnforceIf(z.Not())
            z_vars.append(z)
        model.Add(sum(z_vars) <= 1)

    model.Maximize(sum(y[i] for i in range(1, N + 1)))

    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = time_limit_s
    solver.parameters.num_search_workers = num_workers
    status = solver.Solve(model)
    elapsed = time.time() - t0

    if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        A = [i for i in range(1, N + 1) if solver.Value(y[i]) == 1]
        return {"N": N, "f3": len(A), "A": A,
                "status": "optimal" if status == cp_model.OPTIMAL else "feasible",
                "time_s": elapsed}
    return {"N": N, "status": "timeout" if status == cp_model.UNKNOWN
            else "infeasible", "time_s": elapsed}


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    mode = sys.argv[1]
    if mode == "verify":
        A = [int(x) for x in sys.argv[2:]]
        print({"A": A, "is_b3": is_b3(A), "|triple_sums|": len(triple_sums(A))})
    elif mode == "greedy":
        N = int(sys.argv[2])
        A = b3_greedy(N)
        print({"N": N, "|A|": len(A), "A": A, "is_b3_check": is_b3(A)})
    elif mode == "exact":
        N = int(sys.argv[2])
        tlim = float(sys.argv[3]) if len(sys.argv) > 3 else 60.0
        import json
        print(json.dumps(f3_exact_cpsat(N, time_limit_s=tlim), indent=2,
                         default=str))
    else:
        print(f"Unknown mode: {mode}")
