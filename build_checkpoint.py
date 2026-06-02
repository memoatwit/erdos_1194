"""
Checkpoint-enabled PDS builder for Erdős #1194.
Saves state after each Strategy-2 call so large N can be reached incrementally.

Usage:
  python build_checkpoint.py <target_n>          # run to target, save checkpoint
  python build_checkpoint.py <target_n> --resume # resume from latest checkpoint

Checkpoint file: results/checkpoint_<n>.pkl
"""

import time, math, sys, os, pickle
import numpy as np

_this_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _this_dir)

try:
    from _jit_search import find_valid_b
    _JIT = True
except ImportError:
    _JIT = False

MAX_SCAN = 5_000_000
CKPT_DIR = os.path.join(_this_dir, "results")


def _latest_checkpoint(below_n):
    """Return (n, path) for the highest saved checkpoint below_n, or (0, None)."""
    best_n, best_path = 0, None
    for f in os.listdir(CKPT_DIR):
        if f.startswith("checkpoint_") and f.endswith(".pkl"):
            try:
                n = int(f[len("checkpoint_"):-4])
                if n < below_n and n > best_n:
                    best_n, best_path = n, os.path.join(CKPT_DIR, f)
            except ValueError:
                pass
    return best_n, best_path


def _save_checkpoint(covered, A, A_set, diffs, rep, strat2_count):
    os.makedirs(CKPT_DIR, exist_ok=True)
    path = os.path.join(CKPT_DIR, f"checkpoint_{covered}.pkl")
    with open(path, "wb") as f:
        pickle.dump(dict(covered=covered, A=A, A_set=A_set,
                         diffs=diffs, rep=rep, strat2_count=strat2_count), f,
                    protocol=pickle.HIGHEST_PROTOCOL)
    return path


def build(target_n: int, resume: bool = True, verbose: bool = True,
          ckpt_every: int = 50):
    """
    Build PDS to target_n, resuming from checkpoint if available.
    Saves checkpoint every ckpt_every Strategy-2 calls.
    """
    # ── Try to resume ────────────────────────────────────────────────────────
    start_covered = 0
    A = [1, 2]; A_set = {1, 2}; diffs = {1: (2, 1)}; rep = {1: (2, 1)}
    covered = 1; strat2_count = 0

    if resume:
        ckpt_n, ckpt_path = _latest_checkpoint(target_n + 1)
        while ckpt_path:
            try:
                with open(ckpt_path, "rb") as f:
                    _test = pickle.load(f)
                break  # valid
            except Exception as e:
                print(f"  Skipping corrupted checkpoint {ckpt_path}: {e}")
                ckpt_n, ckpt_path = _latest_checkpoint(ckpt_n)
        if ckpt_path:
            print(f"  Resuming from checkpoint at n={ckpt_n}  ({ckpt_path})")
            with open(ckpt_path, "rb") as f:
                state = pickle.load(f)
            covered       = state["covered"]
            A             = state["A"]
            A_set         = state["A_set"]
            diffs         = state["diffs"]
            rep           = state["rep"]
            strat2_count  = state["strat2_count"]
            start_covered = covered

    t0 = time.time()
    s2_since_ckpt = 0

    while covered < target_n:
        n = covered + 1

        # ── Strategy 1 ───────────────────────────────────────────────────────
        found = False
        for b in sorted(A, reverse=True):
            a = b + n
            if a in A_set:
                continue
            nd = {}; ok = True
            for x in A:
                d = a - x if a > x else x - a
                if d in diffs or d in nd:
                    ok = False; break
                nd[d] = (max(a, x), min(a, x))
            if ok:
                A.append(a); A_set.add(a); diffs.update(nd)
                while covered + 1 in diffs:
                    covered += 1; rep[covered] = diffs[covered]
                found = True; break

        # ── Strategy 2 ───────────────────────────────────────────────────────
        if not found:
            strat2_count += 1; s2_since_ckpt += 1
            max_A    = max(A)
            max_diff = max(diffs.keys())
            diffs_bool = np.zeros(max_diff + 2, dtype=np.bool_)
            for d in diffs:
                diffs_bool[d] = True
            A_arr = np.array(sorted(A), dtype=np.int64)

            if _JIT:
                b = find_valid_b(A_arr, diffs_bool, n, max_A, covered, MAX_SCAN)
            else:
                CHUNK = 2_000; b = -1
                b_start = max_A + covered + 1
                rule3_arr = np.array(sorted(x + n for x in A), dtype=np.int64)
                while b_start <= max_A + MAX_SCAN:
                    b_end = min(b_start + CHUNK, max_A + MAX_SCAN + 1)
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
                        b = int(cands[hit[0]]); break
                    b_start = b_end

            if b == -1:
                b = 2 * max(A)
                while b in A_set or (b + n) in A_set:
                    b += 1
                if verbose:
                    print(f"  [fallback] n={n}")

            a = b + n
            nd_b = {b - x: (b, x) for x in A}
            nd_a = {a - x: (a, x) for x in A}
            nd_a[n] = (a, b)
            A.extend([b, a]); A_set.update([b, a])
            diffs.update(nd_b); diffs.update(nd_a)
            while covered + 1 in diffs:
                covered += 1; rep[covered] = diffs[covered]

            # Periodic checkpoint
            if s2_since_ckpt >= ckpt_every:
                path = _save_checkpoint(covered, A, A_set, diffs, rep, strat2_count)
                elapsed = time.time() - t0
                print(f"  [ckpt n={covered}]  max(A)={max(A)}  "
                      f"s2={strat2_count}  t={elapsed:.1f}s  → {os.path.basename(path)}")
                s2_since_ckpt = 0

    elapsed = time.time() - t0
    print(f"Done in {elapsed:.2f}s (from n={start_covered})  "
          f"|A|={len(A)}  max(A)={max(A)}  JIT={'yes' if _JIT else 'no'}")

    # Final checkpoint
    _save_checkpoint(covered, A, A_set, diffs, rep, strat2_count)

    return sorted(A), rep, strat2_count


def analyze_and_save(rep, A, strat2_count, target_n):
    ns  = sorted(rep.keys())
    N   = max(ns)
    ln  = lambda n: math.log(max(n, 2))
    peaks = []; best = 0
    for n in ns:
        r = rep[n][0] / n**2
        if r > best:
            best = r; peaks.append((n, rep[n][0], r))

    print(f"\n{'─'*70}")
    print(f"  RUNNING PEAKS of a_n")
    print(f"{'─'*70}")
    for n, a, r in peaks[-20:]:
        print(f"  n={n:5d}  a_n={a:12d}  a_n/n²={r:8.4f}  "
              f"a_n/(n²lnN)={a/(n**2*ln(n)):.4f}")

    if len(peaks) >= 8:
        tail = peaks[-20:]
        log_n = [math.log(p[0]) for p in tail]
        log_a = [math.log(p[1]) for p in tail]
        k = len(tail)
        slope = (k*sum(x*y for x,y in zip(log_n,log_a)) - sum(log_n)*sum(log_a)) / \
                (k*sum(x**2 for x in log_n) - sum(log_n)**2)
        inter = (sum(log_a) - slope*sum(log_n)) / k
        print(f"\n  Log-log fit (last {k} peaks):  a_n ~ {math.exp(inter):.4f} · n^{slope:.4f}")

    print(f"\n  |A|={len(A)}  max(A)={max(A)}  s2={strat2_count}")
    print(f"  max(A)/N²={max(A)/N**2:.4f}  "
          f"max(A)/(N²lnN)={max(A)/(N**2*ln(N)):.4f}  "
          f"max(A)/N^2.5={max(A)/N**2.5:.4f}  "
          f"max(A)/N^3={max(A)/N**3:.6f}  "
          f"max(A)/(N^3 lnN)={max(A)/(N**3*ln(N)):.6f}")

    path = os.path.join(CKPT_DIR, f"pds_{target_n}.csv")
    with open(path, "w") as f:
        f.write("n,a_n,b_n,ratio_n2,ratio_n2logn,ratio_n2p5\n")
        for n in sorted(rep.keys()):
            a, b = rep[n]; ln_ = math.log(max(n, 2))
            f.write(f"{n},{a},{b},{a/n**2:.8f},{a/(n**2*ln_):.8f},{a/n**2.5:.8f}\n")
    print(f"  Saved → {path}")


if __name__ == "__main__":
    args = sys.argv[1:]
    resume_flag = "--resume" in args
    args = [a for a in args if a != "--resume"]
    TARGET = int(args[0]) if args else 2000

    print(f"Building PDS to n={TARGET}  (JIT={'yes' if _JIT else 'no'}) ...")
    A, rep, s2 = build(TARGET, resume=resume_flag or True, verbose=False)
    analyze_and_save(rep, A, s2, TARGET)
