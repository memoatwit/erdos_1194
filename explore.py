"""
Erdős Problem #1194 — Computational Exploration (Optimised v4 — numba JIT)
===========================================================================
Perfect difference sets: A ⊂ ℕ where every n ≥ 1 is uniquely a_n - b_n, a_n,b_n ∈ A.
Question: how fast must a_n/n grow?

Strategy 1 (per step):
  For n = covered+1, try a = b+n for each b ∈ A (largest b first).
  a > every existing element, so conflicts are large differences — fast to detect.

Strategy 2 (fresh pair, numba JIT inner loop):
  Build bool_array[0..max_diff] marking which differences are already taken.
  Scan candidates b = max_A + covered + 1, max_A + covered + 2, ... using JIT:
    Rule 1: (b − x) ∉ diffs  for all x ∈ A
    Rule 2: (b+n − x) ∉ diffs  for all x ∈ A
    Rule 3: b ≠ x+n  for any x ∈ A  (else difference n would appear twice)
  Once a valid b is found, add pair (b, b+n) — provably correct, no extra checks.

  Note: we start scanning from max_A + covered + 1, not max_A + 1, because
  any b with b - max_A <= covered means b - max_A is already in diffs
  (max_A ∈ A, and (max_A + k) - max_A = k ≤ covered → k ∈ diffs). So those
  are immediately ruled out by Rule 1, and we skip them.

Proof of Strategy 2 correctness (b > max_A):
  • nd_b = {b-x : x∈A} — distinct positive values not in diffs (Rule 1).
  • nd_a = {(b+n)-x : x∈A} ∪ {n} — n ∉ diffs (uncovered), n ∉ nd_b (Rule 3),
    nd_a ∩ nd_b = ∅ because b-y = (b+n)-x ⟺ n = y-x, which contradicts n ∉ diffs.
  • Rule 2 ensures nd_a ∩ diffs = ∅.
"""

import time
import math
import sys
import os
import numpy as np

# ── numba JIT setup ──────────────────────────────────────────────────────────
# Import from file (not inline) so numba can cache compilation.
_this_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _this_dir)

try:
    from _jit_search import find_valid_b
    _JIT = True
except ImportError:
    _JIT = False

MAX_SCAN = 5_000_000   # hard ceiling for Strategy 2 scan


def build(target_n: int, verbose: bool = False):
    A        = [1, 2]
    A_set    = {1, 2}
    diffs    = {1: (2, 1)}
    rep      = {1: (2, 1)}
    covered  = 1
    strat2_count = 0

    while covered < target_n:
        n = covered + 1

        # ── Strategy 1: a = b+n for existing b ∈ A (largest b first) ────────
        found = False
        for b in sorted(A, reverse=True):
            a = b + n
            if a in A_set:
                continue
            nd = {}
            ok = True
            for x in A:
                d = a - x if a > x else x - a
                if d in diffs or d in nd:
                    ok = False
                    break
                nd[d] = (max(a, x), min(a, x))
            if ok:
                A.append(a); A_set.add(a); diffs.update(nd)
                while covered + 1 in diffs:
                    covered += 1; rep[covered] = diffs[covered]
                found = True
                break

        # ── Strategy 2: JIT or numpy scan ────────────────────────────────────
        if not found:
            strat2_count += 1
            max_A = max(A)

            # Build boolean lookup array for diffs
            max_diff = max(diffs.keys())
            diffs_bool = np.zeros(max_diff + 2, dtype=np.bool_)
            for d in diffs:
                diffs_bool[d] = True

            A_arr = np.array(sorted(A), dtype=np.int64)

            if _JIT:
                b = find_valid_b(A_arr, diffs_bool, n, max_A, covered, MAX_SCAN)
            else:
                # numpy fallback (chunk-based)
                CHUNK = 2_000
                b = -1
                b_start = max_A + covered + 1
                scan_end = max_A + MAX_SCAN
                rule3_arr = np.array(sorted(x + n for x in A), dtype=np.int64)

                while b_start <= scan_end:
                    b_end = min(b_start + CHUNK, scan_end + 1)
                    cands = np.arange(b_start, b_end, dtype=np.int64)

                    deltas_b = cands[:, None] - A_arr[None, :]
                    deltas_a = deltas_b + n

                    in1 = deltas_b <= max_diff
                    flags_b = np.where(in1, diffs_bool[np.where(in1, deltas_b, 0)], False)

                    in2 = (deltas_a >= 0) & (deltas_a <= max_diff)
                    flags_a = np.where(in2, diffs_bool[np.where(in2, deltas_a, 0)], False)

                    valid = ~(np.any(flags_b, axis=1) | np.any(flags_a, axis=1))
                    valid &= ~np.isin(cands, rule3_arr)

                    hit = np.flatnonzero(valid)
                    if hit.size > 0:
                        b = int(cands[hit[0]])
                        break
                    b_start = b_end

            if b == -1:
                # Fallback: b = 2·max(A) always works
                b = 2 * max_A
                while b in A_set or (b + n) in A_set:
                    b += 1
                if verbose:
                    print(f"  [fallback 2·max(A)] n={n}, b={b}")

            a = b + n
            nd_b = {b - x: (b, x) for x in A}
            nd_a = {a - x: (a, x) for x in A}
            nd_a[n] = (a, b)
            A.extend([b, a]); A_set.update([b, a])
            diffs.update(nd_b); diffs.update(nd_a)
            while covered + 1 in diffs:
                covered += 1; rep[covered] = diffs[covered]

    if verbose:
        print(f"  Strategy-2 calls: {strat2_count}  JIT={'yes' if _JIT else 'no (numpy fallback)'}")
    return sorted(A), rep, strat2_count


def analyze(rep, A, strat2_count=0):
    ns   = sorted(rep.keys())
    N    = max(ns)
    ln   = lambda n: math.log(max(n, 2))

    peaks = []
    best  = 0
    for n in ns:
        r = rep[n][0] / n**2
        if r > best:
            best = r
            peaks.append((n, rep[n][0], r))

    print(f"\n{'─'*70}")
    print(f"  RUNNING PEAKS of a_n   (each time a new record a_n/n² is set)")
    print(f"{'─'*70}")
    print(f"  {'n':>5}  {'a_n':>12}  {'a_n/n²':>10}  "
          f"{'a_n/(n²logn)':>14}  {'a_n/n^2.5':>12}")
    for n, a, r in peaks:
        print(f"  {n:>5}  {a:>12}  {r:>10.4f}  "
              f"{a/(n**2*ln(n)):>14.4f}  {a/n**2.5:>12.4f}")

    if len(peaks) >= 8:
        tail = peaks[-min(20, len(peaks)):]
        log_n = [math.log(p[0]) for p in tail]
        log_a = [math.log(p[1]) for p in tail]
        k     = len(tail)
        slope = (k*sum(x*y for x,y in zip(log_n,log_a)) - sum(log_n)*sum(log_a)) / \
                (k*sum(x**2 for x in log_n) - sum(log_n)**2)
        inter = (sum(log_a) - slope*sum(log_n)) / k
        print(f"\n  Log-log fit (last {k} peaks):  a_n ~ {math.exp(inter):.3f} · n^{slope:.4f}")

    print(f"\n  |A|={len(A)},  max(A)={max(A)},  Strategy-2 fires={strat2_count}")
    print(f"  max(A)/N²={max(A)/N**2:.4f},  "
          f"max(A)/(N²·lnN)={max(A)/(N**2*ln(N)):.4f},  "
          f"max(A)/N^2.5={max(A)/N**2.5:.4f},  "
          f"max(A)/N^3={max(A)/N**3:.6f}")


def save_csv(rep, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        f.write("n,a_n,b_n,ratio_n2,ratio_n2logn,ratio_n2p5\n")
        for n in sorted(rep.keys()):
            a, b = rep[n]
            ln = math.log(max(n, 2))
            f.write(f"{n},{a},{b},{a/n**2:.8f},{a/(n**2*ln):.8f},{a/n**2.5:.8f}\n")
    print(f"  Saved → {path}")


if __name__ == "__main__":
    TARGET = int(sys.argv[1]) if len(sys.argv) > 1 else 300

    print(f"Building PDS to n={TARGET}  (JIT={'yes' if _JIT else 'numpy fallback'}) ...")
    t0 = time.time()
    A, rep, s2 = build(TARGET, verbose=True)
    elapsed = time.time() - t0
    print(f"Done in {elapsed:.2f}s  |A|={len(A)}  max(A)={max(A)}")

    analyze(rep, A, s2)
    os.makedirs(os.path.join(_this_dir, "results"), exist_ok=True)
    save_csv(rep, os.path.join(_this_dir, f"results/pds_{TARGET}.csv"))
