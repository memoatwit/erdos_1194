"""
Two-scale shifted-template constructions for Erdős #156.

Idea: combine a small dense Sidon "core" C with a sparse macroscale Sidon
"anchor set" S to form B = a*S + C (Minkowski sum after dilation), so that:

  - Anchor-anchor differences are themselves *designed*, not accidental:
    Δ(B) ⊇ a·Δ(S) translated by Δ(C) and ±Δ(C).
  - Core-core differences pack each tile with small differences {1, ..., δ}.
  - Cross-tile differences fill gaps between successive a·Δ(S) translates.

Anchor candidates:
  - Singer perfect difference set in Z_{q^2+q+1} for prime power q.
    Δ(S) covers every nonzero residue mod (q^2+q+1) exactly once.
  - Erdős–Turán B_2: {2pi + i^2 mod p : 0 ≤ i < p} for prime p.  Sidon, span ~ 2p^2.

Usage:
  python3 erdos_156/two_scale_template.py --c-name 0,1,3,7 --q 3 --a 10
  python3 erdos_156/two_scale_template.py --sweep
"""
from __future__ import annotations

import argparse
import json
import math
import os
from itertools import combinations


THIS_DIR = os.path.dirname(os.path.abspath(__file__))
RESULTS = os.path.join(THIS_DIR, "results")
os.makedirs(RESULTS, exist_ok=True)


# ---------- Sidon machinery (copied for self-containment) ----------
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

def best_admissible_interval(W, max_B):
    """Longest [L,R] in W with L <= 0 and R >= max_B."""
    runs = intervals(W)
    admissible = [(L, R) for (L, R) in runs if L <= 0 and R >= max_B]
    if not admissible:
        return None
    return max(admissible, key=lambda lr: lr[1] - lr[0])


# ---------- Anchor-set generators ----------
def singer_difference_set(q):
    """Return a Singer perfect difference set of size q+1 in Z_{q^2+q+1}.

    Constructed via the (q,q+1) projective geometry trick: take the discrete log
    in F_{q^3}* of the F_q*-cosets.  We use the elementary number-theoretic
    construction: pick a primitive root g of F_{q^3} via cubic field over F_q.
    Here we use the well-known small cases.
    """
    # Hardcoded small Singer sets (perfect difference sets) for prime powers q.
    # Source: classical references; verified by Δ(S) = Z_{q^2+q+1}\{0}.
    table = {
        2: (7,  [0, 1, 3]),                # k=3
        3: (13, [0, 1, 3, 9]),             # k=4
        4: (21, [0, 1, 6, 8, 18]),         # k=5
        5: (31, [0, 1, 3, 8, 12, 18]),     # k=6
        7: (57, [0, 1, 3, 13, 32, 36, 43, 52]),  # k=8
        8: (73, [0, 1, 3, 7, 15, 31, 36, 54, 63]),  # k=9
        9: (91, [0, 1, 3, 9, 27, 49, 56, 61, 77, 81]),  # k=10
        11: (133, [0, 1, 3, 12, 20, 34, 38, 81, 88, 94, 104, 109]),  # k=12
        13: (183, [0, 1, 3, 16, 23, 28, 42, 76, 82, 86, 119, 137, 154, 175]),  # k=14
        16: (273, [0, 1, 3, 7, 15, 31, 63, 90, 116, 127, 136, 181, 194, 204, 233, 238, 255]),  # k=17
    }
    if q not in table:
        raise ValueError(f"No Singer table entry for q={q}; supported: {sorted(table)}")
    return table[q]


def erdos_turan_sidon(p):
    """Erdős-Turán B_2 set: {2pi + (i^2 mod p) : 0 ≤ i < p}.

    Size p, span < 2p^2 + p.  Sidon over Z (not just Z_{2p^2+p}).
    Requires p prime.
    """
    return [2 * p * i + (i * i) % p for i in range(p)]


def verify_singer(M, S):
    """Verify Δ(S) (mod M) hits each of {1..M-1} exactly once."""
    seen = {}
    for i, a in enumerate(S):
        for b in S[i + 1:]:
            for d in [(b - a) % M, (a - b) % M]:
                seen[d] = seen.get(d, 0) + 1
    # Should have each of 1..M-1 exactly once
    target = {x: 1 for x in range(1, M)}
    return seen == target


# ---------- Two-scale composition ----------
def two_scale(core, anchors_int_set, a):
    """B = a * anchors + core (Minkowski sum).  Returns sorted list."""
    B = sorted({a * s + c for s in anchors_int_set for c in core})
    return B


def evaluate(B):
    """Return dict with score info."""
    if not is_sidon(B):
        return {"sidon": False}
    W = blocker_set(B)
    max_B = max(B)
    ai = best_admissible_interval(W, max_B)
    if ai is None:
        return {"sidon": True, "admissible": False, "max_B": max_B}
    L, R = ai
    interval_length = R - L + 1
    k = len(B)
    return {
        "sidon": True,
        "admissible": True,
        "B": B,
        "k": k,
        "max_B": max_B,
        "interval": [L, R],
        "interval_length": interval_length,
        "covered_N": [max_B + 1, R - L + 1],
        "ratio_L_over_k3": interval_length / k**3,
        "ratio_L_log_over_k3": interval_length * math.log(k) / k**3 if k > 1 else 0,
        "ratio_L_log2_over_k3": interval_length * math.log(k)**2 / k**3 if k > 1 else 0,
    }


# ---------- Sweep ----------
CORE_LIBRARY = {
    "C2":   [0, 1],
    "C3":   [0, 1, 3],
    "C4a":  [0, 1, 3, 7],
    "C4b":  [0, 2, 3, 7],
    "C5":   [0, 2, 7, 8, 11],
    "C6":   [0, 1, 3, 7, 12, 20],
    "C7a":  [0, 1, 3, 13, 20, 30, 31],  # may not all be Sidon-friendly
}


def sweep(args):
    rows = []
    q_list = [2, 3, 4, 5, 7, 8, 9, 11, 13, 16]
    if args.q:
        q_list = [args.q]
    for core_name, core in CORE_LIBRARY.items():
        if not is_sidon(core):
            continue
        max_c = max(core)
        for q in q_list:
            try:
                M, S = singer_difference_set(q)
            except ValueError:
                continue
            for a in range(max_c + 1, 3 * max_c + 30):
                B = two_scale(core, S, a)
                if not is_sidon(B):
                    continue
                res = evaluate(B)
                if not res["admissible"]:
                    continue
                res.update({"core": core_name, "q": q, "a": a, "M": M, "S": S})
                rows.append(res)
    # Best by k
    rows.sort(key=lambda r: (r["k"], -r["ratio_L_log2_over_k3"]))
    return rows


def print_rows(rows, top=12):
    if not rows:
        print("No valid two-scale templates with admissible blocker interval.")
        return
    # Sort by L*log^2(k)/k^3 desc
    rows = sorted(rows, key=lambda r: -r["ratio_L_log2_over_k3"])
    print(f"\nTop {top} two-scale templates by L*log^2(k)/k^3:")
    print(f"{'core':>5} {'q':>3} {'a':>4} {'k':>3} {'L':>5} "
          f"{'L/k^3':>7} {'L*log/k^3':>10} {'L*log^2/k^3':>12} "
          f"{'covered N':>14}")
    for r in rows[:top]:
        c = r["covered_N"]
        print(f"{r['core']:>5} {r['q']:>3} {r['a']:>4} {r['k']:>3} {r['interval_length']:>5} "
              f"{r['ratio_L_over_k3']:>7.4f} {r['ratio_L_log_over_k3']:>10.4f} "
              f"{r['ratio_L_log2_over_k3']:>12.4f} {str(c):>14}")


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--core-name", type=str, default=None,
                   help="comma-separated core, e.g. 0,1,3,7")
    p.add_argument("--q", type=int, default=None, help="restrict to one Singer parameter")
    p.add_argument("--a", type=int, default=None, help="dilation factor (single test)")
    p.add_argument("--sweep", action="store_true")
    p.add_argument("--top", type=int, default=15)
    p.add_argument("--output", type=str, default=None)
    args = p.parse_args()

    if args.sweep:
        rows = sweep(args)
        print(f"Found {len(rows)} valid (Sidon, admissible) two-scale templates.")
        print_rows(rows, top=args.top)
        if args.output:
            with open(args.output, "w") as f:
                json.dump(rows, f, indent=2, default=list)
            print(f"\nWrote {args.output}")
        return 0

    # Single test
    if args.core_name is None:
        args.core_name = "0,1,3,7"
    core = sorted(int(v) for v in args.core_name.split(","))
    q = args.q or 3
    a = args.a or (max(core) + 3)
    M, S = singer_difference_set(q)
    print(f"Core: {core}, |core|={len(core)}, span={max(core)}")
    print(f"Singer q={q}: M={M}, S={S}")
    print(f"a={a}")
    B = two_scale(core, S, a)
    print(f"B = {B}")
    res = evaluate(B)
    print(json.dumps(res, indent=2, default=list))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
