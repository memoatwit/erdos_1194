"""
Erdos Problem #156: minimum size of a maximal Sidon set in [1, N].

This first solver is deliberately self-contained: it does not require
ortools.  It enumerates Sidon sets by cardinality using bitsets for
differences, and tests inclusion-maximality at the leaves.

Usage:
  python3 erdos_156/solve_156.py verify 20 1 5 12 18
  python3 erdos_156/solve_156.py hunt 65 6
  python3 erdos_156/solve_156.py milp 70 6 120
  python3 erdos_156/solve_156.py solve 30
  python3 erdos_156/solve_156.py sweep 40
"""
from __future__ import annotations

import itertools
import json
import math
import os
import random
import sys
import time
from dataclasses import dataclass
from typing import Iterable


THIS_DIR = os.path.dirname(os.path.abspath(__file__))
RESULTS = os.path.join(THIS_DIR, "results")


def pair_count(k: int) -> int:
    return k * (k - 1) // 2


def sidon_diff_mask(A: Iterable[int]) -> int | None:
    """Return positive-difference bitmask, or None if A is not Sidon."""
    vals = sorted(A)
    mask = 0
    for j, b in enumerate(vals):
        for a in vals[:j]:
            d = b - a
            bit = 1 << d
            if mask & bit:
                return None
            mask |= bit
    return mask


def is_sidon(A: Iterable[int], N: int | None = None) -> bool:
    vals = list(A)
    if len(vals) != len(set(vals)):
        return False
    if N is not None and any(x < 1 or x > N for x in vals):
        return False
    return sidon_diff_mask(vals) is not None


def addable_reason(x: int, A: list[int], diff_mask: int) -> tuple[bool, str]:
    """Return whether x can be added to Sidon A, plus a short reason.

    If false, reason is one of:
      - "in_A"
      - "existing_difference"
      - "symmetric_collision"
    """
    if x in A:
        return False, "in_A"

    new_mask = 0
    for a in A:
        d = abs(x - a)
        if d == 0:
            return False, "in_A"
        bit = 1 << d
        if diff_mask & bit:
            return False, "existing_difference"
        if new_mask & bit:
            return False, "symmetric_collision"
        new_mask |= bit
    return True, "addable"


def is_maximal_sidon(A: Iterable[int], N: int) -> bool:
    vals = sorted(A)
    diff_mask = sidon_diff_mask(vals)
    if diff_mask is None:
        return False
    present = set(vals)
    for x in range(1, N + 1):
        if x in present:
            continue
        ok, _ = addable_reason(x, vals, diff_mask)
        if ok:
            return False
    return True


def blocking_profile(A: Iterable[int], N: int) -> dict:
    """Count how outside points are blocked."""
    vals = sorted(A)
    diff_mask = sidon_diff_mask(vals)
    if diff_mask is None:
        raise ValueError("A is not Sidon")
    counts = {"in_A": len(vals), "existing_difference": 0,
              "symmetric_collision": 0, "addable": 0}
    examples = {"existing_difference": [], "symmetric_collision": [],
                "addable": []}
    present = set(vals)
    for x in range(1, N + 1):
        if x in present:
            continue
        ok, reason = addable_reason(x, vals, diff_mask)
        if ok:
            reason = "addable"
        counts[reason] += 1
        if reason in examples and len(examples[reason]) < 10:
            examples[reason].append(x)
    return {"counts": counts, "examples": examples}


def blocked_count(A: list[int], N: int, diff_mask: int | None = None) -> int:
    """Number of points in [1,N] that cannot be added to A."""
    if diff_mask is None:
        diff_mask = sidon_diff_mask(A)
        if diff_mask is None:
            return -1
    count = 0
    for x in range(1, N + 1):
        ok, _ = addable_reason(x, A, diff_mask)
        if not ok:
            count += 1
    return count


def maximal_size_lower_bound(N: int) -> int:
    """A safe counting lower bound for maximal Sidon sets.

    A k-element Sidon set has C(k,2) used differences.  A point outside A can
    be blocked either by matching one of these differences against an existing
    element (at most 2k C(k,2) possible positions) or by being the midpoint of
    two elements of A (at most C(k,2) positions).  Therefore
        N <= k + (2k + 1) C(k,2)
    is necessary.
    """
    k = 1
    while k + (2 * k + 1) * pair_count(k) < N:
        k += 1
    return k


def greedy_maximal(N: int, order: list[int]) -> list[int]:
    A: list[int] = []
    diff_mask = 0
    for x in order:
        ok, _ = addable_reason(x, A, diff_mask)
        if not ok:
            continue
        for a in A:
            diff_mask |= 1 << abs(x - a)
        A.append(x)
        A.sort()
    return A


def greedy_upper_bound(N: int, trials: int = 250, seed: int = 156) -> list[int]:
    """Find a decent maximal Sidon set by random greedy trials."""
    rng = random.Random(seed)
    candidates: list[list[int]] = []
    candidates.append(greedy_maximal(N, list(range(1, N + 1))))
    candidates.append(greedy_maximal(N, list(range(N, 0, -1))))
    center_first = sorted(range(1, N + 1), key=lambda x: (abs(2 * x - N - 1), x))
    candidates.append(greedy_maximal(N, center_first))
    for _ in range(trials):
        order = list(range(1, N + 1))
        rng.shuffle(order)
        candidates.append(greedy_maximal(N, order))
    return min(candidates, key=lambda A: (len(A), A))


def _new_diff_bits_for_add(x: int, A: list[int], diff_mask: int) -> int | None:
    """Return new difference bits if x can be added to Sidon A, else None."""
    if x in A:
        return None
    new_bits = 0
    for a in A:
        d = abs(x - a)
        bit = 1 << d
        if (diff_mask | new_bits) & bit:
            return None
        new_bits |= bit
    return new_bits


def hunt_maximal_sidon_of_size(
    N: int,
    k: int,
    trials: int = 20_000,
    top: int = 12,
    seed: int | None = None,
) -> tuple[list[int] | None, dict]:
    """Coverage-first randomized search for a maximal Sidon set of size k.

    This is not a proof of infeasibility when it fails.  It is a fast way to
    find feasible witnesses near the DFS frontier.  At each step it tries all
    legal additions and samples among the top candidates by current blocked
    coverage.
    """
    rng = random.Random(seed if seed is not None else 10_000 * N + k)
    t0 = time.time()
    best_A: list[int] = []
    best_blocked = -1
    best_profile: dict | None = None

    for trial in range(trials):
        A: list[int] = []
        diff_mask = 0
        while len(A) < k:
            candidates = []
            for x in range(1, N + 1):
                new_bits = _new_diff_bits_for_add(x, A, diff_mask)
                if new_bits is None:
                    continue
                next_A = sorted(A + [x])
                next_mask = diff_mask | new_bits
                span = next_A[-1] - next_A[0] if len(next_A) > 1 else 0
                center_pull = -abs(2 * x - N - 1) / max(N, 1)
                score = (
                    blocked_count(next_A, N, next_mask)
                    + 0.03 * span
                    + 0.05 * center_pull
                    + 0.01 * rng.random()
                )
                candidates.append((score, x, new_bits))
            if not candidates:
                break
            candidates.sort(reverse=True)
            _, x, new_bits = rng.choice(candidates[:min(top, len(candidates))])
            diff_mask |= new_bits
            A.append(x)
            A.sort()

        if len(A) != k:
            continue
        now_blocked = blocked_count(A, N, diff_mask)
        if now_blocked > best_blocked:
            best_A = list(A)
            best_blocked = now_blocked
            best_profile = blocking_profile(A, N)
        if now_blocked == N and is_maximal_sidon(A, N):
            return list(A), {
                "status": "feasible",
                "trials": trial + 1,
                "best_blocked": best_blocked,
                "best_A": best_A,
                "best_profile": best_profile,
                "time_s": time.time() - t0,
            }

    return None, {
        "status": "not_found",
        "trials": trials,
        "best_blocked": best_blocked,
        "best_A": best_A,
        "best_profile": best_profile,
        "time_s": time.time() - t0,
    }


def milp_maximal_sidon_of_size(
    N: int,
    k: int,
    time_limit_s: float = 120.0,
) -> tuple[list[int] | None, dict]:
    """MILP feasibility model for a maximal Sidon set of size k.

    Uses scipy.optimize.milp/HiGHS when available.  This is heavier to build
    than the DFS, but it encodes maximality directly and can sometimes prove
    hard fixed-size cases.
    """
    t0 = time.time()
    try:
        import numpy as np
        from scipy.optimize import Bounds, LinearConstraint, milp
        from scipy.sparse import coo_array
    except Exception as exc:  # pragma: no cover - depends on local env
        return None, {
            "status": "unavailable",
            "error": repr(exc),
            "time_s": time.time() - t0,
        }

    # Variable layout: y_i, u_{i,j}, w_{x,a,i,j}.
    y_idx = {i: i - 1 for i in range(1, N + 1)}
    next_idx = N
    pair_idx: dict[tuple[int, int], int] = {}
    pairs_by_diff: dict[int, list[tuple[int, int]]] = {d: [] for d in range(1, N)}
    for i in range(1, N + 1):
        for j in range(i + 1, N + 1):
            pair_idx[(i, j)] = next_idx
            pairs_by_diff[j - i].append((i, j))
            next_idx += 1

    w_terms_by_x: dict[int, list[int]] = {x: [] for x in range(1, N + 1)}
    w_defs: list[tuple[int, int, int]] = []
    for x in range(1, N + 1):
        seen_terms = set()
        for a in range(1, N + 1):
            if a == x:
                continue
            d = abs(x - a)
            for i, j in pairs_by_diff[d]:
                key = (a, pair_idx[(i, j)])
                if key in seen_terms:
                    continue
                seen_terms.add(key)
                w = next_idx
                next_idx += 1
                w_defs.append((w, y_idx[a], pair_idx[(i, j)]))
                w_terms_by_x[x].append(w)

    num_vars = next_idx
    rows: list[int] = []
    cols: list[int] = []
    data: list[float] = []
    lb: list[float] = []
    ub: list[float] = []

    def add_row(coeffs: list[tuple[int, float]], lo: float, hi: float) -> None:
        r = len(lb)
        for c, v in coeffs:
            rows.append(r)
            cols.append(c)
            data.append(v)
        lb.append(lo)
        ub.append(hi)

    inf = float("inf")

    # Cardinality.
    add_row([(y_idx[i], 1.0) for i in range(1, N + 1)], float(k), float(k))

    # u_{i,j} = y_i AND y_j.
    for (i, j), u in pair_idx.items():
        add_row([(u, 1.0), (y_idx[i], -1.0)], -inf, 0.0)
        add_row([(u, 1.0), (y_idx[j], -1.0)], -inf, 0.0)
        add_row([(u, 1.0), (y_idx[i], -1.0), (y_idx[j], -1.0)], -1.0, inf)

    # Sidon: at most one pair for each positive difference.
    for d, pairs in pairs_by_diff.items():
        add_row([(pair_idx[p], 1.0) for p in pairs], -inf, 1.0)

    # w = y_a AND u_pair for existing-difference blockers.
    for w, ya, u in w_defs:
        add_row([(w, 1.0), (ya, -1.0)], -inf, 0.0)
        add_row([(w, 1.0), (u, -1.0)], -inf, 0.0)
        add_row([(w, 1.0), (ya, -1.0), (u, -1.0)], -1.0, inf)

    # Maximality: x is in A, or some existing-difference blocker exists, or
    # x is the midpoint of a pair of elements of A.
    for x in range(1, N + 1):
        coeffs = [(y_idx[x], 1.0)]
        coeffs.extend((w, 1.0) for w in w_terms_by_x[x])
        for a in range(1, x):
            b = 2 * x - a
            if x < b <= N:
                coeffs.append((pair_idx[(a, b)], 1.0))
        add_row(coeffs, 1.0, inf)

    constraints = LinearConstraint(
        coo_array((data, (rows, cols)), shape=(len(lb), num_vars)).tocsr(),
        np.array(lb),
        np.array(ub),
    )
    c = np.zeros(num_vars)
    bounds = Bounds(np.zeros(num_vars), np.ones(num_vars))
    integrality = np.ones(num_vars)

    result = milp(
        c=c,
        integrality=integrality,
        bounds=bounds,
        constraints=constraints,
        options={"time_limit": time_limit_s, "mip_rel_gap": 0.0},
    )
    elapsed = time.time() - t0
    stats = {
        "status": str(result.message),
        "success": bool(result.success),
        "time_s": elapsed,
        "num_vars": num_vars,
        "num_constraints": len(lb),
        "fun": None if result.fun is None else float(result.fun),
        "mip_node_count": getattr(result, "mip_node_count", None),
        "mip_dual_bound": getattr(result, "mip_dual_bound", None),
        "mip_gap": getattr(result, "mip_gap", None),
    }
    if not result.success or result.x is None:
        return None, stats

    A = [i for i in range(1, N + 1) if result.x[y_idx[i]] > 0.5]
    if len(A) == k and is_maximal_sidon(A, N):
        stats["status"] = "feasible"
        return A, stats
    stats["decoded_A"] = A
    stats["decoded_is_sidon"] = is_sidon(A, N)
    stats["decoded_is_maximal"] = is_maximal_sidon(A, N) if is_sidon(A, N) else False
    return None, stats


@dataclass
class SearchStats:
    nodes: int = 0
    leaves: int = 0
    sidon_prunes: int = 0
    maximal_hits: int = 0
    elapsed_s: float = 0.0
    status: str = "unknown"


def find_maximal_sidon_of_size(
    N: int,
    k: int,
    time_limit_s: float = 30.0,
    coverage_order: bool = False,
) -> tuple[list[int] | None, SearchStats]:
    """Find a maximal Sidon set of size exactly k, if one is found."""
    t0 = time.time()
    deadline = t0 + time_limit_s
    stats = SearchStats()

    # Tiny symmetry break under reflection x -> N+1-x:
    # for nonempty sets, require min(A) <= N+1-max(A).  We only test at leaves,
    # so this never removes both members of a reflection pair.
    def leaf_symmetry_ok(A: list[int]) -> bool:
        return not A or A[0] <= N + 1 - A[-1]

    def dfs(start: int, A: list[int], diff_mask: int) -> list[int] | str | None:
        if time.time() > deadline:
            return "TIMEOUT"
        stats.nodes += 1

        need = k - len(A)
        if need == 0:
            stats.leaves += 1
            if not leaf_symmetry_ok(A):
                return None
            if is_maximal_sidon(A, N):
                stats.maximal_hits += 1
                return list(A)
            return None
        if N - start + 1 < need:
            return None

        last_start = N - need + 1
        candidates = []
        for x in range(start, last_start + 1):
            new_bits = 0
            collide = False
            for a in A:
                d = x - a
                bit = 1 << d
                if (diff_mask | new_bits) & bit:
                    collide = True
                    break
                new_bits |= bit
            if collide:
                stats.sidon_prunes += 1
                continue
            if coverage_order:
                next_A = A + [x]
                next_mask = diff_mask | new_bits
                span = next_A[-1] - next_A[0] if len(next_A) > 1 else 0
                score = blocked_count(next_A, N, next_mask) + 0.03 * span
                candidates.append((score, x, new_bits))
            else:
                candidates.append((0.0, x, new_bits))

        if coverage_order:
            candidates.sort(reverse=True)

        # If this partial set is already not Sidon we pruned when generating
        # candidates.  Try all increasing extensions, optionally coverage-first.
        for _, x, new_bits in candidates:
            A.append(x)
            result = dfs(x + 1, A, diff_mask | new_bits)
            A.pop()
            if result == "TIMEOUT":
                return result
            if result is not None:
                return result
        return None

    result = dfs(1, [], 0)
    stats.elapsed_s = time.time() - t0
    if result == "TIMEOUT":
        stats.status = "timeout"
        return None, stats
    if result is not None:
        stats.status = "feasible"
        return result, stats
    stats.status = "infeasible"
    return None, stats


def solve_exact(
    N: int,
    time_limit_per_k: float = 30.0,
    greedy_trials: int = 250,
    hunt_trials_per_k: int = 5_000,
) -> dict:
    os.makedirs(RESULTS, exist_ok=True)
    t0 = time.time()
    upper = greedy_upper_bound(N, trials=greedy_trials)
    k_lo = maximal_size_lower_bound(N)
    k_hi = len(upper)
    log = []

    for k in range(k_lo, k_hi + 1):
        hunt_log = None
        if hunt_trials_per_k > 0 and k > k_lo:
            A, hunt_log = hunt_maximal_sidon_of_size(
                N, k, trials=hunt_trials_per_k, seed=10_000 * N + k
            )
            if A is not None:
                result = {
                    "N": N,
                    "status": "solved",
                    "m": len(A),
                    "A": A,
                    "lower_bound_start": k_lo,
                    "greedy_upper": len(upper),
                    "greedy_A": upper,
                    "profile": blocking_profile(A, N),
                    "log": log + [{
                        "k": k,
                        "status": "feasible",
                        "method": "hunt",
                        **hunt_log,
                    }],
                    "total_time_s": time.time() - t0,
                }
                return result

        A, stats = find_maximal_sidon_of_size(
            N, k, time_limit_s=time_limit_per_k, coverage_order=(k > k_lo)
        )
        entry = {
            "k": k,
            "status": stats.status,
            "method": "dfs",
            "nodes": stats.nodes,
            "leaves": stats.leaves,
            "sidon_prunes": stats.sidon_prunes,
            "time_s": stats.elapsed_s,
        }
        if hunt_log is not None:
            entry["hunt"] = hunt_log
        log.append(entry)
        if A is not None:
            result = {
                "N": N,
                "status": "solved",
                "m": len(A),
                "A": A,
                "lower_bound_start": k_lo,
                "greedy_upper": len(upper),
                "greedy_A": upper,
                "profile": blocking_profile(A, N),
                "log": log,
                "total_time_s": time.time() - t0,
            }
            return result
        if stats.status == "timeout":
            return {
                "N": N,
                "status": "timeout",
                "lower_bound_start": k_lo,
                "greedy_upper": len(upper),
                "greedy_A": upper,
                "log": log,
                "total_time_s": time.time() - t0,
            }

    # Greedy upper bound is always maximal, so reaching here certifies it.
    return {
        "N": N,
        "status": "solved",
        "m": len(upper),
        "A": upper,
        "lower_bound_start": k_lo,
        "greedy_upper": len(upper),
        "greedy_A": upper,
        "profile": blocking_profile(upper, N),
        "log": log,
        "total_time_s": time.time() - t0,
    }


def save_result(result: dict) -> None:
    os.makedirs(RESULTS, exist_ok=True)
    path = os.path.join(RESULTS, f"exact_156_N{result['N']}.json")
    with open(path, "w") as f:
        json.dump(result, f, indent=2, default=str)


def print_result(result: dict) -> None:
    N = result["N"]
    print(f"N={N} status={result['status']} total={result['total_time_s']:.2f}s")
    print(f"  lower_bound_start={result['lower_bound_start']}")
    print(f"  greedy_upper={result['greedy_upper']} greedy_A={result['greedy_A']}")
    if result["status"] == "solved":
        m = result["m"]
        print(f"  m(N)={m}  A={result['A']}")
        print(f"  m/N^(1/3)={m / (N ** (1/3)):.4f}")
        print(f"  m/(N log N)^(1/3)={m / ((N * math.log(max(N, 2))) ** (1/3)):.4f}")
        print(f"  profile={result['profile']['counts']}")
    for row in result["log"]:
        method = row.get("method", "dfs")
        if method == "hunt":
            print("   "
                  f"k={row['k']:2d} {row['status']:>10s} "
                  f"method=hunt trials={row['trials']:7d} "
                  f"best_blocked={row['best_blocked']:3d} "
                  f"t={row['time_s']:.2f}s")
        else:
            print("   "
                  f"k={row['k']:2d} {row['status']:>10s} "
                  f"method=dfs nodes={row['nodes']:8d} "
                  f"leaves={row['leaves']:7d} t={row['time_s']:.2f}s")


def write_summary(results: list[dict]) -> None:
    os.makedirs(RESULTS, exist_ok=True)
    solved = [r for r in results if r.get("status") == "solved"]
    path_json = os.path.join(RESULTS, "exact_156.json")
    with open(path_json, "w") as f:
        json.dump(results, f, indent=2, default=str)

    lines = [
        "# Erdős #156 exact-search summary",
        "",
        "Computed by `erdos_156/solve_156.py` using a self-contained bitset DFS.",
        "",
        "| N | status | m(N) | witness A | m/N^(1/3) | m/(N log N)^(1/3) |",
        "|---:|---|---:|---|---:|---:|",
    ]
    for r in results:
        if r.get("status") == "solved":
            N = r["N"]
            m = r["m"]
            lines.append(
                f"| {N} | solved | {m} | `{r['A']}` | "
                f"{m / (N ** (1/3)):.4f} | "
                f"{m / ((N * math.log(max(N, 2))) ** (1/3)):.4f} |"
            )
        else:
            lines.append(
                f"| {r['N']} | {r.get('status')} | - | - | - | - |"
            )
    lines.extend([
        "",
        "## Notes",
        "",
        "- `m(N)` is the minimum size of an inclusion-maximal Sidon subset of `[1,N]`.",
        "- Finite exact data is only a structure-finding tool; it is not by itself progress on the asymptotic problem.",
    ])
    path_md = os.path.join(RESULTS, "exact_156_summary.md")
    with open(path_md, "w") as f:
        f.write("\n".join(lines) + "\n")


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print(__doc__)
        return 1
    mode = argv[1]
    if mode == "verify":
        if len(argv) < 4:
            print("Usage: verify N a1 a2 ...")
            return 1
        N = int(argv[2])
        A = [int(x) for x in argv[3:]]
        print(json.dumps({
            "N": N,
            "A": A,
            "is_sidon": is_sidon(A, N),
            "is_maximal_sidon": is_maximal_sidon(A, N),
            "profile": blocking_profile(A, N) if is_sidon(A, N) else None,
        }, indent=2))
        return 0
    if mode == "solve":
        N = int(argv[2])
        time_limit = float(argv[3]) if len(argv) > 3 else 30.0
        result = solve_exact(N, time_limit_per_k=time_limit)
        save_result(result)
        print_result(result)
        return 0
    if mode == "hunt":
        if len(argv) < 4:
            print("Usage: hunt N k [trials]")
            return 1
        N = int(argv[2])
        k = int(argv[3])
        trials = int(argv[4]) if len(argv) > 4 else 20_000
        A, stats = hunt_maximal_sidon_of_size(N, k, trials=trials)
        print(json.dumps({"N": N, "k": k, "A": A, **stats}, indent=2,
                         default=str))
        return 0
    if mode == "milp":
        if len(argv) < 4:
            print("Usage: milp N k [time_limit_s]")
            return 1
        N = int(argv[2])
        k = int(argv[3])
        time_limit = float(argv[4]) if len(argv) > 4 else 120.0
        A, stats = milp_maximal_sidon_of_size(N, k, time_limit_s=time_limit)
        print(json.dumps({
            "N": N,
            "k": k,
            "A": A,
            "profile": blocking_profile(A, N) if A else None,
            **stats,
        }, indent=2, default=str))
        return 0
    if mode == "sweep":
        N_max = int(argv[2])
        time_limit = float(argv[3]) if len(argv) > 3 else 30.0
        Ns = [N for N in range(5, N_max + 1, 5)]
        results = []
        for N in Ns:
            print("=" * 72)
            result = solve_exact(N, time_limit_per_k=time_limit)
            save_result(result)
            print_result(result)
            results.append(result)
            if result.get("status") == "timeout":
                break
        write_summary(results)
        return 0
    print(f"Unknown mode: {mode}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
