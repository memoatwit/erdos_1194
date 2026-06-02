"""
Phase 3' — dense-Sidon-seeded greedy.

Take a dense Sidon set as the initial A and greedy-complete it to a
PDS covering [1, N]. Measure resulting max(A) and compare to from-scratch
greedy.

Three seed families:
  1. Mian-Chowla:        {1, 2, 5, 10, 11, 13, 37, ...} (greedy Sidon)
  2. Erdős-Turán:        {2pi + (i^2 mod p) : i = 0..p-1} for prime p
                          (size p in [1, 2p^2 + p])
  3. Singer:             explicit difference set in Z/(q^2+q+1) for prime
                          power q, size q+1.  Lifted to Z.

Usage:
  python3 seeded_greedy.py mian 500
  python3 seeded_greedy.py erdos_turan 13 500       # Erdős-Turán p=13, target N=500
  python3 seeded_greedy.py singer 7 500             # Singer q=7, target N=500
"""
from __future__ import annotations
import os, sys, csv, math, time

THIS_DIR = os.path.dirname(os.path.abspath(__file__))
RESULTS  = os.path.join(THIS_DIR, "results")


# ────────────────────────────────────────────────────────────────────
# Dense Sidon seeds
# ────────────────────────────────────────────────────────────────────
PHASE4_OPTIMA = {
    20: [1, 5, 6, 18, 20, 26, 29, 36],
    25: [1, 3, 11, 25, 26, 30, 37, 43, 46],
    30: [1, 2, 7, 11, 24, 27, 35, 42, 54, 56],
    35: [1, 2, 7, 11, 24, 27, 35, 42, 54, 56],
    40: [1, 10, 11, 18, 31, 43, 46, 57, 62, 80, 84, 86],
    45: [1, 10, 11, 18, 31, 43, 46, 57, 62, 80, 84, 86],
}


def phase4_seed(N_seed: int) -> list[int]:
    if N_seed not in PHASE4_OPTIMA:
        raise ValueError(f"No Phase 4 optimum stored for N={N_seed}")
    return list(PHASE4_OPTIMA[N_seed])


def mian_chowla(n_elements: int) -> list[int]:
    """Greedy Sidon set: pick smallest x not creating a difference clash."""
    A = [1]
    diffs = set()
    while len(A) < n_elements:
        x = A[-1] + 1
        while True:
            new_d = set()
            ok = True
            for a in A:
                d = x - a
                if d in diffs or d in new_d:
                    ok = False
                    break
                new_d.add(d)
            if ok:
                A.append(x)
                diffs |= new_d
                break
            x += 1
    return A


def erdos_turan(p: int) -> list[int]:
    """Erdős-Turán Sidon set in [1, 2p^2 + p]: {2pi + (i^2 mod p) + 1 : i = 0..p-1}."""
    return sorted(set(2 * p * i + (i * i) % p + 1 for i in range(p)))


def singer(q: int) -> list[int]:
    """Singer difference set placeholder — would need field-based construction.
    Not currently implemented (table entries unverified)."""
    raise NotImplementedError("Singer construction needs field-arithmetic; use Erdős-Turán instead.")


# ────────────────────────────────────────────────────────────────────
# Seeded greedy: complete A_seed to a PDS covering [1, N]
# ────────────────────────────────────────────────────────────────────
def seeded_greedy(A_seed: list[int], target_N: int, verbose: bool = False):
    """Extend A_seed to cover differences [1, target_N], following greedy
    Strategy 1 / Strategy 2 logic (analogous to explore.py).
    Returns sorted A, rep dict, strat2_count.
    """
    A = list(A_seed)
    A_set = set(A_seed)
    diffs = {}
    rep = {}
    for j in range(len(A)):
        for i in range(j):
            d = A[j] - A[i]
            diffs[d] = (A[j], A[i])
            if d <= target_N:
                rep[d] = (A[j], A[i])
    covered = 0
    while covered + 1 in rep:
        covered += 1
    strat2_count = 0
    t0 = time.time()
    while covered < target_N:
        n = covered + 1
        # Strategy 1: a = b + n for b in A, biggest first
        found = False
        for b in sorted(A, reverse=True):
            a = b + n
            if a in A_set:
                continue
            new_d = {}
            ok = True
            for x in A:
                d = a - x if a > x else x - a
                if d in diffs or d in new_d:
                    ok = False
                    break
                new_d[d] = (max(a, x), min(a, x))
            if ok:
                A.append(a)
                A_set.add(a)
                for d, p in new_d.items():
                    diffs[d] = p
                    if d <= target_N:
                        rep.setdefault(d, p)
                while covered + 1 in rep:
                    covered += 1
                found = True
                break
        if found:
            continue
        # Strategy 2: introduce a fresh pair (b, b+n) for smallest valid b.
        strat2_count += 1
        max_A = max(A)
        b = max_A + covered + 1
        scan_limit = max_A * 100
        while b <= scan_limit:
            a = b + n
            ok = True
            new_d = {}
            for x in A:
                for y in (b, a):
                    d = y - x if y > x else x - y
                    if d in diffs or d in new_d:
                        ok = False
                        break
                if not ok:
                    break
            if ok:
                # also check b - a = -n; the new pair contributes diff n
                if n in diffs or n in new_d:
                    ok = False
            if ok:
                # also check b ≠ x + n (would cause Rule 3 issue): handle by checking diff n in new_d
                new_d[n] = (a, b)
                A.extend([b, a])
                A_set.update([b, a])
                for d, p in new_d.items():
                    diffs[d] = p
                    if d <= target_N:
                        rep.setdefault(d, p)
                while covered + 1 in rep:
                    covered += 1
                break
            b += 1
        if b > scan_limit:
            raise RuntimeError(f"Strategy 2 stuck at n={n}, b > {scan_limit}")
        if verbose and strat2_count % 50 == 0:
            print(f"  strat2={strat2_count}, n={n}, |A|={len(A)}, "
                  f"max(A)={max(A)}, t={time.time()-t0:.1f}s",
                  flush=True)
    return sorted(A), rep, strat2_count


# ────────────────────────────────────────────────────────────────────
# Main
# ────────────────────────────────────────────────────────────────────
def main():
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(1)
    seed_kind = sys.argv[1]
    target_N = int(sys.argv[-1])
    if seed_kind == "mian":
        n_seed = int(sys.argv[2]) if len(sys.argv) >= 4 else 20
        A_seed = mian_chowla(n_seed)
        seed_desc = f"mian_chowla(n={n_seed})"
    elif seed_kind == "erdos_turan":
        p = int(sys.argv[2])
        A_seed = erdos_turan(p)
        seed_desc = f"erdos_turan(p={p})"
    elif seed_kind == "singer":
        q = int(sys.argv[2])
        A_seed = singer(q)
        seed_desc = f"singer(q={q})"
    elif seed_kind == "phase4":
        N0 = int(sys.argv[2])
        A_seed = phase4_seed(N0)
        seed_desc = f"phase4(N0={N0})"
    else:
        print(f"Unknown seed kind: {seed_kind}")
        sys.exit(1)

    # Check seed is Sidon (sanity)
    seen = set()
    ok_sidon = True
    for i, a in enumerate(A_seed):
        for j, b in enumerate(A_seed):
            if j >= i: break
            d = a - b
            if d in seen:
                ok_sidon = False
                break
            seen.add(d)
        if not ok_sidon: break
    if not ok_sidon:
        print(f"ERROR: seed {seed_desc} is not Sidon!")
        sys.exit(1)

    print(f"=" * 70)
    print(f" Phase 3' — seeded greedy: seed = {seed_desc}, target N = {target_N}")
    print(f"=" * 70)
    print(f"  seed: |A_seed|={len(A_seed)}, max(A_seed)={max(A_seed)}")
    print(f"  seed elements: {A_seed[:20]}{'...' if len(A_seed) > 20 else ''}")
    # Diffs covered by seed
    seed_diffs = set()
    for i, a in enumerate(A_seed):
        for j, b in enumerate(A_seed):
            if j >= i: break
            seed_diffs.add(a - b)
    cov = 0
    while cov + 1 in seed_diffs:
        cov += 1
    print(f"  seed covers [1, {cov}] for free")
    print(f"  Running seeded greedy...", flush=True)
    t0 = time.time()
    A_final, rep, s2 = seeded_greedy(A_seed, target_N, verbose=True)
    t = time.time() - t0
    print(f"  Done in {t:.1f}s.")
    print(f"  |A_final| = {len(A_final)},  max(A_final) = {max(A_final):,}")
    print(f"  Strategy-2 fires: {s2}")
    # Peak a_n analysis
    peak_ratios = []
    running_max_a = 0
    for n in range(1, target_N + 1):
        if n in rep:
            a = rep[n][0]
            if a > running_max_a:
                running_max_a = a
                peak_ratios.append((n, a, a / n**2, a / n**3))
    print(f"  Peaks (last 10): n, a_n, a_n/n^2, a_n/n^3")
    for n, a, r2, r3 in peak_ratios[-10:]:
        print(f"    n={n:5d}  a_n={a:10d}  a_n/n^2={r2:8.4f}  a_n/n^3={r3:.6f}")
    print(f"  max a_n /target_N^3 = {max(rep[n][0] for n in rep) / target_N**3:.6f}")
    # Save CSV
    safe = seed_desc.replace("(","_").replace(")","").replace("=","").replace(",","_")
    out = os.path.join(RESULTS, f"seeded_{safe}_N{target_N}.csv")
    with open(out, "w") as f:
        w = csv.writer(f)
        w.writerow(["n", "a_n", "b_n"])
        for n in sorted(rep.keys()):
            a, b = rep[n]
            w.writerow([n, a, b])
    print(f"  Saved → {out}")


if __name__ == "__main__":
    main()
