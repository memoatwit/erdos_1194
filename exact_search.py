"""
Phase 4 — exact branch-and-bound for PDS minimizing max(A).

Find the smallest M such that there exists A subset of [1, M] with:
  - 1 in A, M in A,
  - A is Sidon (all pairwise differences distinct),
  - every n in [1, N] is realised as a - b for some a, b in A.

Strategy: scan M = M_lo, M_lo + 1, ... upward.  For each M, run a depth-first
search for a Sidon A subset [1, M] with {1, M} <= A and [1, N] subset A - A.
First feasible M is the optimum.

Differences and A are stored as Python big-integer bitmasks for speed.

Pruning per M:
  - Sidon: every new difference must not already be set.
  - Slot capacity: free difference slots in [1, M-1] >= |needed|.
  - Smallest-uncovered reachability: u_min must be reachable by some future
    single insertion x in (last_x, M), or by a future pair fitting in (last_x, M).

Usage:
  python3 exact_search.py 20 30 50

Outputs results/exact_N{N}.json.

The script supports incremental runs: each invocation reads existing
exact_N{N}.json, picks up at the next untested M, and writes back.
"""
from __future__ import annotations
import sys
import json
import time
import math
import os

THIS_DIR = os.path.dirname(os.path.abspath(__file__))
RESULTS  = os.path.join(THIS_DIR, "results")


def lower_bound_M(N: int) -> int:
    K_min  = math.ceil((1 + math.sqrt(1 + 8 * N)) / 2)
    M_lo_1 = N + 1
    M_lo_2 = 1 + K_min * (K_min - 1) // 2
    return max(M_lo_1, M_lo_2)


def search_pds(N: int, M: int, time_budget_s: float = 60.0
               ) -> tuple[list[int] | None, dict]:
    """Find Sidon A subset [1, M] with {1, M} <= A and [1, N] subset A - A."""
    t0       = time.time()
    deadline = t0 + time_budget_s
    nodes    = [0]
    stats    = {"nodes": 0, "time_s": 0.0, "status": "infeasible"}

    if M < N + 1:
        return None, {"nodes": 0, "time_s": 0.0, "status": "infeasible"}

    target_mask = (1 << (N + 1)) - 2          # bits 1..N

    A_init      = [1, M]
    A_mask_init = (1 << 1) | (1 << M)
    diffs_init  = 1 << (M - 1)
    needed_init = target_mask & ~diffs_init
    if needed_init == 0:
        return A_init, {"nodes": 0, "time_s": 0.0, "status": "feasible"}

    def _dfs(A: list[int], A_mask: int, diffs: int, needed: int,
             last_x: int):
        if time.time() > deadline:
            return "TIMEOUT"
        nodes[0] += 1

        if needed == 0:
            return list(A)

        used = bin(diffs).count("1")
        needed_cnt = bin(needed).count("1")
        if (M - 1) - used < needed_cnt:
            return None

        u_min = (needed & -needed).bit_length() - 1

        # u_min reachability: some future x in (last_x, M) covers u_min as
        # x - a = u_min OR a - x = u_min for some a in A.
        reachable = False
        for a in A:
            xa = a + u_min
            if last_x < xa < M and not ((A_mask >> xa) & 1):
                reachable = True; break
            xb = a - u_min
            if last_x < xb < M and not ((A_mask >> xb) & 1):
                reachable = True; break
        if not reachable and u_min > (M - 1) - (last_x + 1):
            return None

        # Reversal symmetry break: at the FIRST branching step (when
        # |A| == 2, i.e. A == [1, M]), require x_2 <= (M+1)/2.
        # The map A -> {M+1-a : a in A} is also a PDS-up-to-N with same
        # difference set; one of the two has x_2 <= (M+1)/2.
        if len(A) == 2:
            x_hi_sym = (M + 1) // 2
        else:
            x_hi_sym = M - 1
        for x in range(last_x + 1, x_hi_sym + 1):
            if (A_mask >> x) & 1:
                continue
            # Compute new differences from x to each element of A.
            new_diffs_mask = 0
            collide = False
            for a in A:
                d = x - a if x > a else a - x
                bit = 1 << d
                if (diffs | new_diffs_mask) & bit:
                    collide = True; break
                new_diffs_mask |= bit
            if collide:
                continue

            new_diffs  = diffs | new_diffs_mask
            new_needed = needed & ~new_diffs_mask
            new_A_mask = A_mask | (1 << x)
            new_A      = A[:-1] + [x, A[-1]]   # M is at the end

            result = _dfs(new_A, new_A_mask, new_diffs, new_needed, x)
            if result == "TIMEOUT":
                return "TIMEOUT"
            if result is not None:
                return result

        return None

    result = _dfs(A_init, A_mask_init, diffs_init, needed_init, last_x=1)
    elapsed = time.time() - t0
    stats["nodes"]  = nodes[0]
    stats["time_s"] = elapsed
    if result == "TIMEOUT":
        stats["status"] = "timeout"
        return None, stats
    if result is not None:
        stats["status"] = "feasible"
        return result, stats
    stats["status"] = "infeasible"
    return None, stats


def solve_exact(N: int, M_hi: int | None = None,
                time_budget_per_M: float = 60.0,
                total_budget_s: float = 600.0,
                verbose: bool = True,
                resume: bool = True) -> dict:
    """Scan M upward; return on first feasible.

    With resume=True, picks up from any saved partial run in
    results/exact_N{N}.json.
    """
    M_lo = lower_bound_M(N)
    if M_hi is None:
        M_hi = 100 * N
    log = []
    if resume:
        path = os.path.join(RESULTS, f"exact_N{N}.json")
        if os.path.exists(path):
            try:
                prev = json.load(open(path))
                if prev.get("status") == "solved":
                    print(f"[N={N}] already solved at M = {prev['M_opt']}")
                    return prev
                log = prev.get("log", [])
                last_tested = max((e["M"] for e in log), default=M_lo - 1)
                M_lo = last_tested + 1
            except Exception:
                pass
    if verbose:
        print(f"[N={N}] M scan starting at {M_lo}")

    save_path = os.path.join(RESULTS, f"exact_N{N}.json")
    t_global = time.time()
    deadline = t_global + total_budget_s
    for M in range(M_lo, M_hi + 1):
        if time.time() > deadline:
            partial = {"N": N, "status": "global_timeout", "log": log}
            with open(save_path, "w") as f:
                json.dump(partial, f, indent=2, default=str)
            return partial
        budget = min(time_budget_per_M, deadline - time.time())
        if verbose:
            print(f"  M = {M:5d} ...", end="", flush=True)
        A, stats = search_pds(N, M, time_budget_s=budget)
        log.append({"M": M, **stats, "A_len": (len(A) if A else None)})
        if verbose:
            print(f"  {stats['status']:>11s}  nodes={stats['nodes']:>10d}  "
                  f"t={stats['time_s']:.3f}s"
                  + (f"  |A|={len(A)}" if A else ""))
        # incremental save for resume support
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
        print(f" PHASE 4 EXACT SEARCH for N = {N}")
        print("=" * 70)
        result = solve_exact(N, time_budget_per_M=120.0, total_budget_s=300.0,
                             resume=True)
        print()
        print(f"  RESULT for N={N}: {result.get('status')}")
        if result.get("M_opt"):
            print(f"  Optimal max(A) = {result['M_opt']}")
            print(f"  Optimal A      = {result['A_opt']}")
            print(f"  |A_opt|        = {len(result['A_opt'])}")
        out = os.path.join(RESULTS, f"exact_N{N}.json")
        with open(out, "w") as f:
            json.dump(result, f, indent=2, default=str)
        print(f"  Saved → {out}")
