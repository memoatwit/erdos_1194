"""
Independent verifier for Erdős covering systems.

Input: JSON file containing a list of [a, n] integer pairs, representing
congruence classes a (mod n).  Optionally the JSON may be a dict with key
"system" pointing to the list.

Checks:
  1. All moduli distinct.
  2. All moduli positive.
  3. min/max modulus.
  4. The union covers Z, equivalently Z/L for L = lcm of moduli.

Coverage is verified by direct simulation in [0, L) using a NumPy boolean
array.  For each pair (a, n) we mark `cover[a::n] = True`, which is a
slice assignment of L/n elements — very fast.  Scales to L up to ~10^9
on a 16GB machine.

Falls back to a pure-Python bytearray bitset if NumPy is unavailable.

Usage:
  python3 verify_covering.py system.json
  echo '[[0,2],[0,3],[1,4],[1,6],[11,12]]' | python3 verify_covering.py -
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from math import gcd


try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False


def lcm(a, b):
    return a // gcd(a, b) * b


def lcm_list(ns):
    L = 1
    for n in ns:
        L = lcm(L, n)
    return L


def verify_numpy(pairs, L):
    """Use NumPy slice assignment; O(sum L/n_i) writes."""
    cover = np.zeros(L, dtype=bool)
    for a, n in pairs:
        a %= n
        cover[a::n] = True
    if cover.all():
        return None  # no uncovered
    # Find first few uncovered positions
    where = np.where(~cover)[0]
    return where[:16].tolist()


def verify_python(pairs, L):
    """Pure-Python bitset fallback."""
    covered = bytearray((L + 7) // 8)
    for a, n in pairs:
        a %= n
        x = a
        while x < L:
            covered[x >> 3] |= 1 << (x & 7)
            x += n
    uncovered = []
    for i in range(L):
        if not (covered[i >> 3] & (1 << (i & 7))):
            uncovered.append(i)
            if len(uncovered) >= 16:
                break
    return uncovered if uncovered else None


def verify(pairs):
    """Return a dict with full verification result."""
    if not pairs:
        return {"ok": False, "error": "empty system"}

    moduli = [n for _, n in pairs]
    if any(n <= 0 for n in moduli):
        return {"ok": False, "error": "non-positive modulus"}

    if len(set(moduli)) != len(moduli):
        from collections import Counter
        c = Counter(moduli)
        dups = sorted(m for m, k in c.items() if k > 1)
        return {"ok": False, "error": "duplicate moduli", "duplicates": dups}

    min_n = min(moduli)
    max_n = max(moduli)
    L = lcm_list(moduli)

    if L > 4 * 10**9:
        return {
            "ok": None,
            "error": f"L = {L} > 4 * 10^9; cannot verify by direct simulation",
            "min_modulus": min_n,
            "max_modulus": max_n,
            "lcm": L,
            "n_congruences": len(pairs),
        }

    t0 = time.time()
    if HAS_NUMPY:
        uncov = verify_numpy(pairs, L)
        backend = "numpy"
    else:
        uncov = verify_python(pairs, L)
        backend = "python"
    t1 = time.time()

    return {
        "ok": uncov is None,
        "n_congruences": len(pairs),
        "min_modulus": min_n,
        "max_modulus": max_n,
        "lcm": L,
        "uncovered_sample": uncov,
        "verify_seconds": round(t1 - t0, 3),
        "backend": backend,
    }


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("input", help="JSON file with list of [a, n] pairs, or '-' for stdin")
    p.add_argument("--quiet", action="store_true")
    args = p.parse_args()

    data = sys.stdin.read() if args.input == "-" else open(args.input).read()
    raw = json.loads(data)
    if isinstance(raw, dict) and "system" in raw:
        raw = raw["system"]
    pairs = [(int(a), int(n)) for a, n in raw]

    res = verify(pairs)
    if not args.quiet:
        print(json.dumps(res, indent=2))
        if res.get("ok"):
            print(f"\n[OK] {res['n_congruences']} congruences, "
                  f"min modulus {res['min_modulus']}, max modulus {res['max_modulus']}, "
                  f"lcm {res['lcm']}, verified in {res['verify_seconds']}s.")
        else:
            print(f"\n[FAIL] {res.get('error') or 'uncovered residues exist'}")
    return 0 if res.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
