"""
Independent verifier for a candidate 3-AP-free subset of {1..N}.

Input: JSON file or stdin containing either
  - a list of integers (the candidate subset A);
  - or a dict {"N": N, "A": [..]} including the universe size.

Checks:
  1. All elements are distinct positive integers.
  2. (If N given) all elements lie in [1..N].
  3. No three elements a < b < c satisfy a + c = 2b.

Output: JSON report with size, is_3ap_free, and (if not) a witnessing triple.

Usage:
  python3 r3_verify.py candidate.json
  echo '[1, 2, 4]' | python3 r3_verify.py -
  echo '{"N": 10, "A": [1, 2, 5, 8]}' | python3 r3_verify.py -
"""
from __future__ import annotations

import argparse
import json
import sys


def is_three_ap_free(A: list[int]) -> tuple[bool, tuple[int, int, int] | None]:
    """Return (True, None) if A is 3-AP-free; else (False, (a, b, c))."""
    S = set(A)
    sorted_A = sorted(set(A))
    # For each pair (a, c) with a < c and a+c even, check if b = (a+c)/2 is in S.
    # O(|A|^2) but with early exit.
    for i, a in enumerate(sorted_A):
        for c in sorted_A[i + 1:]:
            if (a + c) % 2:
                continue
            b = (a + c) // 2
            if b == a or b == c:
                continue
            if b in S:
                return False, (a, b, c)
    return True, None


def verify(A: list[int], N: int | None = None) -> dict:
    if not A:
        return {
            "ok": True, "size": 0, "is_3ap_free": True,
            "witness_triple": None,
            "note": "empty set is trivially 3-AP-free",
        }
    if len(set(A)) != len(A):
        from collections import Counter
        dups = sorted(x for x, k in Counter(A).items() if k > 1)
        return {"ok": False, "error": "duplicate elements", "duplicates": dups}
    if any(not isinstance(x, int) or x < 1 for x in A):
        return {"ok": False, "error": "elements must be positive integers"}
    if N is not None:
        outside = [x for x in A if x > N]
        if outside:
            return {"ok": False, "error": f"elements outside [1..{N}]",
                    "offenders": outside[:8]}
    ok, witness = is_three_ap_free(A)
    return {
        "ok": ok,
        "size": len(A),
        "N": N,
        "min": min(A),
        "max": max(A),
        "is_3ap_free": ok,
        "witness_triple": list(witness) if witness else None,
    }


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("input", help="JSON file or '-' for stdin")
    p.add_argument("--quiet", action="store_true")
    args = p.parse_args()

    data = sys.stdin.read() if args.input == "-" else open(args.input).read()
    raw = json.loads(data)
    N = None
    if isinstance(raw, dict):
        N = raw.get("N")
        A = raw.get("A")
        if A is None:
            print("[FAIL] dict must contain 'A' key", file=sys.stderr)
            return 2
    else:
        A = raw

    A = [int(x) for x in A]
    res = verify(A, N=N)
    if not args.quiet:
        print(json.dumps(res, indent=2))
        if res.get("ok") and res.get("is_3ap_free"):
            print(f"\n[OK] |A| = {res['size']} elements in [{res['min']}, {res['max']}], 3-AP-free.")
        else:
            print(f"\n[FAIL] {res.get('error') or 'AP triple: ' + str(res.get('witness_triple'))}")
    return 0 if res.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
