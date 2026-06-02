"""
Exhaustive local repair around a fixed Sidon near-miss.

Usage:
  python3 erdos_156/local_repair_156.py N radius a1 a2 ...
"""
from __future__ import annotations

import itertools
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from repair_125_k8 import addable_points, profile, score, diff_mask


def local_repair(N: int, A: list[int], radius: int) -> dict:
    t0 = time.time()
    k = len(A)
    A = sorted(A)
    best_A = tuple(A)
    best_score = score(best_A, N)
    checked = 0
    legal = 0

    universe = set(range(1, N + 1))
    for r in range(1, radius + 1):
        for remove in itertools.combinations(A, r):
            base = [x for x in A if x not in remove]
            available = sorted(universe - set(base))
            for add in itertools.combinations(available, r):
                nxt = tuple(sorted(base + list(add)))
                checked += 1
                if len(set(nxt)) != k or diff_mask(nxt) is None:
                    continue
                legal += 1
                b = score(nxt, N)
                if b > best_score:
                    best_score = b
                    best_A = nxt
                    if b == N:
                        return {
                            "N": N,
                            "k": k,
                            "radius": radius,
                            "status": "feasible",
                            "time_s": time.time() - t0,
                            "checked": checked,
                            "legal": legal,
                            "best_blocked": best_score,
                            "best_A": list(best_A),
                            "best_profile": profile(best_A, N),
                        }

    return {
        "N": N,
        "k": k,
        "radius": radius,
        "status": "not_found",
        "time_s": time.time() - t0,
        "checked": checked,
        "legal": legal,
        "best_blocked": best_score,
        "best_A": list(best_A),
        "best_addable": addable_points(best_A, N),
        "best_profile": profile(best_A, N),
    }


def main(argv: list[str]) -> int:
    if len(argv) < 4:
        print(__doc__)
        return 2
    N = int(argv[1])
    radius = int(argv[2])
    A = [int(x) for x in argv[3:]]
    print(json.dumps(local_repair(N, A, radius), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
