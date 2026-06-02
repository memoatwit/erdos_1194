"""
Search for size-(k+1) extensions of a given size-k Sidon template B that
extend the consecutive interval inside the relative blocker set W(B).

The size-8 template B = [0, 40, 60, 61, 63, 67, 96, 112] gives
W(B) ⊃ [-7, 136], which is an interval of length 144. Adding one more
element to B may push that interval longer; this script tries every
candidate.

Specifically:
  - For each x not in B, x ∈ [lo, hi]:
      * check B ∪ {x} is Sidon;
      * compute W(B ∪ {x});
      * record the longest consecutive interval inside the new W.
  - Report the best extensions by interval length.

Usage:
  python3 extend_template.py
  python3 extend_template.py --B 0,40,60,61,63,67,96,112 --lo -200 --hi 300
  python3 extend_template.py --top 20
"""
from __future__ import annotations
import argparse
import json
from itertools import combinations


DEFAULT_B = [0, 40, 60, 61, 63, 67, 96, 112]


def intervals(vals):
    xs = sorted(set(vals))
    if not xs:
        return []
    out = []
    start = prev = xs[0]
    for x in xs[1:]:
        if x == prev + 1:
            prev = x
        else:
            out.append((start, prev))
            start = prev = x
    out.append((start, prev))
    return out


def diffs_of(B):
    return {b - a for a, b in combinations(sorted(B), 2)}


def is_sidon(B):
    d = [b - a for a, b in combinations(sorted(B), 2)]
    return len(d) == len(set(d))


def blocker_set(B):
    B = sorted(B)
    D = sorted(diffs_of(B))
    W = set(B)
    for b in B:
        for d in D:
            W.add(b - d)
            W.add(b + d)
    for a, b in combinations(B, 2):
        if (a + b) % 2 == 0:
            W.add((a + b) // 2)
    return W


def longest_interval_through(W, anchor=0):
    """Return (L, R) the longest interval in W that contains `anchor`.
    If no interval contains anchor, return the globally longest."""
    runs = intervals(W)
    if not runs:
        return None
    # prefer interval containing 0 (anchor)
    for (L, R) in runs:
        if L <= anchor <= R:
            return (L, R)
    return max(runs, key=lambda lr: lr[1] - lr[0])


def evaluate_extension(B, x):
    """Return data about B' = B ∪ {x}: Sidon, longest interval through 0,
    length, etc. None if B' not Sidon."""
    if x in B:
        return None
    Bp = sorted(set(B) | {x})
    if not is_sidon(Bp):
        return None
    W = blocker_set(Bp)
    # interval that contains both 0 and max(B') would be ideal for the lemma
    runs = intervals(W)
    # the "useful" interval is one with L ≤ 0 and R ≥ max(B')
    max_b = max(Bp)
    useful = [(L, R) for (L, R) in runs if L <= 0 and R >= max_b]
    longest_useful = max(useful, key=lambda lr: lr[1] - lr[0]) if useful else None
    longest_through_0 = longest_interval_through(W, 0)
    longest_overall = max(runs, key=lambda lr: lr[1] - lr[0]) if runs else None
    return {
        "x": x,
        "B_prime": Bp,
        "max_B_prime": max_b,
        "W_size": len(W),
        "longest_overall": longest_overall,
        "longest_through_0": longest_through_0,
        "longest_useful": longest_useful,
        "N_max_by_useful": (longest_useful[1] + 1 - longest_useful[0]
                            if longest_useful else None),
    }


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--B", type=str, default=",".join(str(v) for v in DEFAULT_B),
                   help="base template, comma-separated (default size-8 template)")
    p.add_argument("--lo", type=int, default=-100,
                   help="lower bound on x scan range (default -100)")
    p.add_argument("--hi", type=int, default=300,
                   help="upper bound on x scan range (default 300)")
    p.add_argument("--top", type=int, default=15,
                   help="how many top extensions to print (default 15)")
    p.add_argument("--json", action="store_true")
    args = p.parse_args()

    B = sorted(int(v) for v in args.B.split(",") if v.strip())
    base_W = blocker_set(B)
    base_runs = intervals(base_W)
    base_longest_overall = max(base_runs, key=lambda lr: lr[1] - lr[0])
    base_longest_useful = [(L, R) for (L, R) in base_runs
                            if L <= 0 and R >= max(B)]
    base_lu = (max(base_longest_useful, key=lambda lr: lr[1] - lr[0])
               if base_longest_useful else None)

    print(f"Base template B = {B}")
    print(f"|W(B)| = {len(base_W)}, longest interval overall: "
          f"{base_longest_overall} (length {base_longest_overall[1] - base_longest_overall[0] + 1})")
    print(f"  longest interval with L<=0 and R>=max(B)={max(B)}: {base_lu}")
    if base_lu:
        print(f"  N covered: [{max(B) + 1}, {base_lu[1] + 1 - base_lu[0]}]")
    print()
    print(f"Scanning x in [{args.lo}, {args.hi}] for extensions...")

    results = []
    for x in range(args.lo, args.hi + 1):
        r = evaluate_extension(B, x)
        if r is None:
            continue
        results.append(r)

    # Sort by useful interval length, then by overall.
    def score(r):
        u = r["longest_useful"]
        useful_len = (u[1] - u[0] + 1) if u else 0
        return (useful_len, r["longest_overall"][1] - r["longest_overall"][0] + 1)

    results.sort(key=score, reverse=True)

    if args.json:
        print(json.dumps(results[:args.top], indent=2, default=str))
        return 0

    print(f"\nFound {len(results)} valid (Sidon) extensions. Top {args.top}:")
    print(f"{'x':>5} {'len(useful)':>11} {'useful [L,R]':>16} {'N_max':>6} "
          f"{'len(overall)':>13} {'overall [L,R]':>17} {'B prime':>}")
    for r in results[:args.top]:
        u = r["longest_useful"]
        ulen = (u[1] - u[0] + 1) if u else 0
        o = r["longest_overall"]
        olen = o[1] - o[0] + 1
        Nmax = r["N_max_by_useful"]
        print(f"{r['x']:>5} {ulen:>11} {str(u or '-'):>16} {str(Nmax or '-'):>6} "
              f"{olen:>13} {str(o):>17}  {r['B_prime']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
