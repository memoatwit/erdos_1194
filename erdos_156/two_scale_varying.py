"""
B': Per-anchor-varying two-scale construction.

Take a Singer anchor set S of size q+1, dilate by a, and pair each anchor s
with one extra element s + d_s where d_s is a *distinct* small offset per
anchor.  Within-tile diffs are {d_{s_1}, d_{s_2}, ..., d_{s_n}} — all
distinct, since the d's are distinct.  This breaks the duplicate-diff
problem of plain Minkowski sum a*S + C.

Construction:
  B = (a*S) union (a*S + d_assignment)
  where d_assignment: S -> distinct small ints (alphabet Σ ⊂ {1..D})

Size: 2|S| if all d_s are nonzero (we allow d_s = 0 = "no extra element").

Search: random/greedy over d-assignments.

Usage:
  python3 erdos_156/two_scale_varying.py --q 7 --a 80 --trials 5000
  python3 erdos_156/two_scale_varying.py --sweep
"""
from __future__ import annotations

import argparse
import json
import math
import os
import random
from itertools import combinations

import two_scale_template as ts


THIS_DIR = os.path.dirname(os.path.abspath(__file__))
RESULTS = os.path.join(THIS_DIR, "results")


def make_template(S, a, d_assignment):
    """B = (a*s, a*s + d_s) for each s in S where d_s is nonzero;
    just a*s if d_s == 0."""
    B = set()
    for s, d in zip(S, d_assignment):
        B.add(a * s)
        if d > 0:
            B.add(a * s + d)
    return sorted(B)


def score(B):
    if not B or not ts.is_sidon(B):
        return None
    W = ts.blocker_set(B)
    max_B = max(B)
    ai = ts.best_admissible_interval(W, max_B)
    if ai is None:
        return None
    L, R = ai
    Lint = R - L + 1
    k = len(B)
    return {
        "B": B,
        "k": k,
        "max_B": max_B,
        "interval": [L, R],
        "interval_length": Lint,
        "ratio_L_over_k3": Lint / k**3 if k else 0,
        "ratio_L_log_over_k3": Lint * math.log(k) / k**3 if k > 1 else 0,
        "ratio_L_log2_over_k3": Lint * math.log(k)**2 / k**3 if k > 1 else 0,
    }


def search_one(q, a, trials, alphabet, seed=0):
    """Random search over distinct d_s assignments from an alphabet.

    The d's are drawn distinctly from `alphabet` (with 0 allowed
    representing 'no extra element')."""
    rng = random.Random(seed)
    M, S = ts.singer_difference_set(q)
    n = len(S)
    if len(alphabet) < n:
        # extend alphabet (we'll just allow duplicates if needed)
        pass
    best = None
    for _ in range(trials):
        # Choose d_s distinct from alphabet (drop if alphabet too small)
        choices = list(alphabet)
        rng.shuffle(choices)
        d = choices[:n]
        B = make_template(S, a, d)
        res = score(B)
        if res is None:
            continue
        if best is None or res["ratio_L_log2_over_k3"] > best["ratio_L_log2_over_k3"]:
            res["d_assignment"] = d
            res["q"] = q
            res["a"] = a
            best = res
    return best


def sweep(args):
    rows = []
    # Alphabets: try a few different small alphabets including 0 (no extra)
    alphabets = {
        "alph_0_1_3_5_7":      [0, 1, 3, 5, 7],
        "alph_0_1_3_5_7_11":   [0, 1, 3, 5, 7, 11],
        "alph_0_1_3_7_12_20":  [0, 1, 3, 7, 12, 20],
        "alph_0_2_5_11_13_17": [0, 2, 5, 11, 13, 17],
    }
    q_list = [3, 5, 7, 8, 9, 11, 13]
    if args.q:
        q_list = [args.q]
    for q in q_list:
        try:
            M, S_set = ts.singer_difference_set(q)
        except ValueError:
            continue
        n = len(S_set)
        # Pick a values that give breathing room: a >= 2*max(alphabet)+1
        for alph_name, alph in alphabets.items():
            if len(alph) < n:
                continue  # need enough distinct offsets
            a_min = 2 * max(alph) + 1
            for a in [a_min, a_min + 5, a_min + 10, 2 * a_min, 3 * a_min]:
                best = search_one(q, a, args.trials, alph, seed=42)
                if best is None:
                    continue
                best.update({"alphabet": alph_name})
                rows.append(best)
                if args.verbose:
                    print(f'q={q} a={a:>3} alph={alph_name:>22}: '
                          f'k={best["k"]:>2}, L={best["interval_length"]:>4}, '
                          f'L/k^3={best["ratio_L_over_k3"]:.3f}, '
                          f'L*log^2/k^3={best["ratio_L_log2_over_k3"]:.3f}')
    return rows


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--q", type=int, default=None)
    p.add_argument("--a", type=int, default=None)
    p.add_argument("--trials", type=int, default=2000)
    p.add_argument("--sweep", action="store_true")
    p.add_argument("--top", type=int, default=15)
    p.add_argument("--verbose", action="store_true")
    p.add_argument("--output", type=str, default=None)
    args = p.parse_args()

    if args.sweep:
        rows = sweep(args)
        print(f"\nTotal valid templates found: {len(rows)}")
        if rows:
            rows = sorted(rows, key=lambda r: -r["ratio_L_log2_over_k3"])
            print(f"\nTop {args.top} by L*log^2(k)/k^3:")
            print(f"{'q':>3} {'a':>4} {'alphabet':>22} {'k':>3} {'L':>5} "
                  f"{'L/k^3':>7} {'L*log/k^3':>10} {'L*log^2/k^3':>12} "
                  f"{'covered':>14}")
            for r in rows[:args.top]:
                covered = [r['max_B']+1, r['interval'][1]+1-r['interval'][0]]
                print(f"{r['q']:>3} {r['a']:>4} {r['alphabet']:>22} {r['k']:>3} "
                      f"{r['interval_length']:>5} {r['ratio_L_over_k3']:>7.4f} "
                      f"{r['ratio_L_log_over_k3']:>10.4f} {r['ratio_L_log2_over_k3']:>12.4f} "
                      f"{str(covered):>14}")
        if args.output:
            with open(args.output, "w") as f:
                json.dump(rows, f, indent=2, default=list)
            print(f"\nWrote {args.output}")
        return 0

    # Single test
    q = args.q or 5
    M, S = ts.singer_difference_set(q)
    a = args.a or (2 * 11 + 1)
    alph = [0, 1, 3, 5, 7, 11]
    best = search_one(q, a, args.trials, alph, seed=42)
    if best is None:
        print("No valid template found.")
    else:
        print(json.dumps(best, indent=2, default=list))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
