"""
Reference exact DFS for r_3(N).

Backtracks element-by-element through {1..N}, maintaining the partial set A.
At each step, either include x = current candidate or skip it.  Include only
if A ∪ {x} stays 3-AP-free, i.e. no 'a, b, x' with a + x = 2b.

Pruning: at depth x, the remaining candidates are {x+1, ..., N}, so the best
possible size is |A| + (N - x).  If that does not exceed the current best,
backtrack.

Slow above ~N = 50.  For larger N use r3_cpsat.py.

Usage:
  python3 r3_brute.py 30          # compute r_3(30)
  python3 r3_brute.py 30 --witness
  python3 r3_brute.py --range 0 35
"""
from __future__ import annotations

import argparse
import json
import sys
import time


def r3_brute(N: int, find_witness: bool = False) -> tuple[int, list[int] | None]:
    """Return (r_3(N), witness) where witness is one optimal set or None."""
    if N <= 0:
        return 0, []

    best_size = 0
    best_witness: list[int] | None = []

    A: list[int] = []
    # For fast extension check: maintain a set of values, and also a set of
    # pairs (used by AP creation check).
    A_set: set[int] = set()
    # For each pair (a, b) in A with a<b, the third AP-element a + 2*(b-a) = 2b - a
    # would form an AP with a, b.  We pre-store all such "forbidden completions".
    # That set has size O(|A|^2) and is small.
    forbidden: set[int] = set()
    # Also need the reverse: a - (b - a) = 2a - b for AP-prev (if a, b are the
    # second and third of an AP, prev is 2a-b).  Actually for an AP triple
    # (p, q, r) with p<q<r, we need to forbid x = r if {p, q, x = 2q-p} \subset A.
    # If we add x, and there exist a, b in A with a + x = 2b (i.e. b = (a+x)/2),
    # then we have an AP.  So when considering adding x, check whether any
    # b = (a + x)/2 is in A for some a in A with same parity.

    def can_add(x: int) -> bool:
        # x makes an AP with a, b iff a + x = 2b and a < b < x  or  b = (a+x)/2 in A.
        # Equivalently, for some a in A, b = (a+x)/2 is in A (and a != x, b != x).
        # Iterate over a in A; check b = (a+x)/2 in A.
        # Also: could x be the middle of an AP a, x, c with a, c in A?
        # That gives c = 2x - a; if both a and c in A, x is the middle.
        for a in A_set:
            if a == x:
                continue
            # x as the LARGEST of an AP: a + x = 2b, so b = (a+x)/2.
            if (a + x) % 2 == 0:
                b = (a + x) // 2
                if b != a and b != x and b in A_set:
                    return False
            # x as the MIDDLE: a + c = 2x, c = 2x - a.
            c = 2 * x - a
            if c != a and c != x and c in A_set:
                return False
            # x as the SMALLEST: x + c = 2b, c in A, b in A.
            # This is the same as the first case with roles swapped, so covered.
        return True

    def dfs(start: int):
        nonlocal best_size, best_witness
        remaining = N - start + 1
        if len(A) + remaining <= best_size:
            return
        if start > N:
            if len(A) > best_size:
                best_size = len(A)
                if find_witness:
                    best_witness = list(A)
            return
        # Try adding x = start
        x = start
        if can_add(x):
            A.append(x)
            A_set.add(x)
            dfs(start + 1)
            A_set.discard(x)
            A.pop()
        # Try skipping x
        dfs(start + 1)

    dfs(1)
    return best_size, best_witness


# Reference values from OEIS A003002 (n = 0..77, from the search result)
OEIS_A003002 = [
    0, 1, 2, 2, 3, 4, 4, 4, 4, 5, 5, 6, 6, 7, 8, 8, 8, 8, 8, 8,
    9, 9, 9, 9, 10, 10, 11, 11, 11, 11, 12, 12, 13, 13, 13, 13, 14, 14, 14, 14,
    15, 16, 16, 16, 16, 16, 16, 16, 16, 16, 16, 17, 17, 17, 18, 18, 18, 18, 19, 19,
    19, 19, 19, 20, 20, 20, 20, 20, 20, 20, 20, 21, 21, 21, 22, 22, 22, 22,
]


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("N", type=int, nargs="?", default=None)
    p.add_argument("--range", type=int, nargs=2, default=None,
                   help="compute r_3(N) for N in [start, end] inclusive")
    p.add_argument("--witness", action="store_true",
                   help="also output one optimal witness set")
    p.add_argument("--check-oeis", action="store_true",
                   help="cross-check computed values against OEIS A003002")
    p.add_argument("--quiet", action="store_true")
    args = p.parse_args()

    if args.range:
        a, b = args.range
        out = []
        ok = True
        for N in range(a, b + 1):
            t0 = time.time()
            size, witness = r3_brute(N, find_witness=args.witness)
            dt = time.time() - t0
            row = {"N": N, "r_3": size, "seconds": round(dt, 4)}
            if args.witness:
                row["witness"] = witness
            if args.check_oeis and 0 <= N < len(OEIS_A003002):
                row["oeis"] = OEIS_A003002[N]
                row["matches_oeis"] = (size == OEIS_A003002[N])
                if size != OEIS_A003002[N]:
                    ok = False
            out.append(row)
            if not args.quiet:
                tag = ""
                if "matches_oeis" in row:
                    tag = " ✓" if row["matches_oeis"] else " ✗"
                print(f"r_3({N}) = {size}{tag}  ({row['seconds']}s)"
                      + (f"  witness={witness}" if args.witness else ""))
        if args.check_oeis:
            print(f"\nAll OEIS A003002 values match: {ok}")
        return 0 if ok else 1
    elif args.N is not None:
        t0 = time.time()
        size, witness = r3_brute(args.N, find_witness=args.witness)
        dt = time.time() - t0
        result = {"N": args.N, "r_3": size, "seconds": round(dt, 4)}
        if args.witness:
            result["witness"] = witness
        if 0 <= args.N < len(OEIS_A003002):
            result["oeis"] = OEIS_A003002[args.N]
            result["matches_oeis"] = (size == OEIS_A003002[args.N])
        print(json.dumps(result, indent=2))
        return 0
    else:
        print("specify N or --range a b", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
