"""
Heuristic hunt for maximal Sidon sets of fixed size, enforcing inclusion
of a "tight pair" (a, a+gap) for small gap. Every size-7 witness we've
found through N=100 has a tight pair with gap 1 or 2.

Usage:  python3 hunt_tight_pair.py N k trials [seed]
"""
from __future__ import annotations
import sys, time, json, random
sys.path.insert(0, ".")
from solve_156 import (sidon_diff_mask, addable_reason, blocked_count,
                       is_maximal_sidon, _new_diff_bits_for_add,
                       blocking_profile)


def hunt_with_tight_pair(N: int, k: int, trials: int = 5000,
                         seed: int = 156) -> dict:
    rng = random.Random(seed)
    t0 = time.time()
    best_blocked = -1
    best_A = []
    best_addable = None

    for trial in range(trials):
        # Choose a tight pair (a, a + gap) with gap ∈ {1, 2}.
        gap = rng.choice([1, 2])
        a_start = rng.randint(1, N - gap)
        seed_pair = [a_start, a_start + gap]
        A = list(seed_pair)
        diff_mask = 1 << gap

        while len(A) < k:
            cands = []
            for x in range(1, N + 1):
                nb = _new_diff_bits_for_add(x, A, diff_mask)
                if nb is None:
                    continue
                next_A = sorted(A + [x])
                next_mask = diff_mask | nb
                bcount = blocked_count(next_A, N, next_mask)
                cands.append((bcount + 0.01 * rng.random(), x, nb))
            if not cands:
                break
            cands.sort(reverse=True)
            top = cands[:min(8, len(cands))]
            _, x, nb = rng.choice(top)
            diff_mask |= nb
            A.append(x); A.sort()

        if len(A) != k:
            continue
        b = blocked_count(A, N, diff_mask)
        if b > best_blocked:
            best_blocked = b
            best_A = list(A)
            if is_maximal_sidon(A, N):
                return {
                    "status": "feasible", "N": N, "k": k,
                    "A": list(A), "trials": trial + 1,
                    "time_s": time.time() - t0,
                }

    # Final: examine best near-miss
    if best_A:
        dm = sidon_diff_mask(best_A)
        addable = [x for x in range(1, N + 1) if x not in best_A
                   and addable_reason(x, best_A, dm)[0]]
    else:
        addable = []

    return {
        "status": "not_found", "N": N, "k": k,
        "best_A": best_A, "best_blocked": best_blocked,
        "best_addable": addable, "trials": trials,
        "time_s": time.time() - t0,
    }


if __name__ == "__main__":
    if len(sys.argv) < 4:
        print(__doc__)
        sys.exit(1)
    N = int(sys.argv[1])
    k = int(sys.argv[2])
    trials = int(sys.argv[3])
    seed = int(sys.argv[4]) if len(sys.argv) > 4 else 156
    r = hunt_with_tight_pair(N, k, trials=trials, seed=seed)
    print(json.dumps(r, indent=2, default=str))
