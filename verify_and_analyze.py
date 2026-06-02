"""
Phase 0 (verify) + Phase 1 (candidate-measure scan, stratification) for #1194.

Loads the largest checkpoint and runs:
  1. Correctness verification of the greedy PDS:
     - every n in [1, covered] is represented exactly once,
     - every recorded difference appears at most once,
     - rep[n] = (a, b) satisfies a > b, a, b in A, a - b == n.
  2. Candidate-measure sums sum_{a in A} 1/a^s for s in {1.0, 1.5, 2.0, 2.5, 3.0}
     and 1/(a (log a)^s) for s in {1, 2}, computed cumulatively over the
     elements of A in order of insertion / by value.
  3. Running min / running max of a_n / n^k for k in {1, 2, 3}, plus the
     stratification of "easy" (Strategy-1-like, a_n small) vs "hard" (a_n
     large) differences.
  4. Number of "hard" n with a_n / n^2 above thresholds.

Outputs:
  - prints a verification report,
  - writes results/measure_sums.csv,
  - writes results/stratified_peaks.csv,
  - writes results/running_min_max.csv,
  - writes results/verification_report.txt.
"""
import os
import math
import pickle
import csv

THIS_DIR = os.path.dirname(os.path.abspath(__file__))
RESULTS  = os.path.join(THIS_DIR, "results")


def latest_checkpoint(dir_):
    """Return (n, path) for the highest checkpoint that loads cleanly."""
    candidates = []
    for f in os.listdir(dir_):
        if f.startswith("checkpoint_") and f.endswith(".pkl"):
            try:
                n = int(f[len("checkpoint_"):-4])
                candidates.append((n, os.path.join(dir_, f)))
            except ValueError:
                pass
    candidates.sort(reverse=True)
    for n, path in candidates:
        try:
            with open(path, "rb") as g:
                pickle.load(g)
            return n, path
        except Exception as e:
            print(f"  Skipping corrupted checkpoint {os.path.basename(path)}: {e}")
    return 0, None


def verify(state):
    """Return (ok: bool, report: list[str])."""
    A           = state["A"]
    A_set       = state["A_set"]
    diffs       = state["diffs"]
    rep         = state["rep"]
    covered     = state["covered"]
    s2          = state["strat2_count"]

    report = []
    ok     = True

    A_sorted = sorted(A)
    A_set_check = set(A)

    if len(A_set_check) != len(A):
        ok = False
        report.append(f"FAIL: |A| has duplicates ({len(A)} list vs {len(A_set_check)} set)")
    else:
        report.append(f"OK  : |A| = {len(A)} distinct elements, max(A) = {max(A)}")

    # Every n in 1..covered is in rep
    missing = [n for n in range(1, covered + 1) if n not in rep]
    if missing:
        ok = False
        report.append(f"FAIL: {len(missing)} missing n in rep, e.g. {missing[:10]}")
    else:
        report.append(f"OK  : every n in [1, {covered}] is in rep")

    # rep[n] = (a, b): a > b, both in A, a - b == n
    bad_rep = []
    for n in range(1, covered + 1):
        a, b = rep[n]
        if not (a > b and a in A_set_check and b in A_set_check and a - b == n):
            bad_rep.append((n, a, b))
            if len(bad_rep) >= 5:
                break
    if bad_rep:
        ok = False
        report.append(f"FAIL: malformed rep entries (first 5): {bad_rep}")
    else:
        report.append(f"OK  : all rep[n] = (a,b) satisfy a-b=n, a,b in A")

    # All pairwise differences from A are distinct (Sidon condition)
    diff_count = {}
    Alist = sorted(A_set_check)
    # only check pairs (a, b) with a > b giving differences <= covered
    # to bound work; for full Sidon check we'd need all pairs.
    # For the PDS condition, we want: every n in [1, covered] has exactly one pair.
    pair_count_for_n = {n: 0 for n in range(1, covered + 1)}
    # Build set lookup
    A_set_lookup = A_set_check
    for b in Alist:
        for a in Alist:
            if a <= b:
                continue
            n = a - b
            if 1 <= n <= covered:
                pair_count_for_n[n] = pair_count_for_n.get(n, 0) + 1

    bad_unique = [(n, c) for n, c in pair_count_for_n.items() if c != 1]
    if bad_unique:
        ok = False
        report.append(f"FAIL: {len(bad_unique)} differences in [1, {covered}] not represented exactly once")
        report.append(f"      first 10: {bad_unique[:10]}")
    else:
        report.append(f"OK  : every n in [1, {covered}] has EXACTLY one pair (a,b) in A")

    # Pairwise differences for n > covered should also be distinct (Sidon)
    sidon_seen = {}
    sidon_violations = 0
    for i in range(len(Alist)):
        for j in range(i + 1, len(Alist)):
            d = Alist[j] - Alist[i]
            if d in sidon_seen:
                sidon_violations += 1
            else:
                sidon_seen[d] = (Alist[j], Alist[i])
    if sidon_violations:
        ok = False
        report.append(f"FAIL: {sidon_violations} repeated differences (Sidon violation)")
    else:
        report.append(f"OK  : all C(|A|,2) = {len(Alist)*(len(Alist)-1)//2} pairwise differences are distinct (Sidon)")

    report.append(f"INFO: Strategy-2 calls = {s2}")
    report.append(f"INFO: |A| = {len(A)}, covered = {covered}, max(A) = {max(A)}")
    return ok, report


def measure_sums(A, rep, covered):
    """Compute partial sums of various candidate measures."""
    Alist = sorted(A)
    Aset  = set(A)

    # Restrict to elements that are actually a_n or b_n for some n <= covered.
    # All of A should be in here (either a_n or b_n for some n).
    # We sum over elements of A in increasing order and report the partial sums
    # up to a_max for several thresholds.

    thresholds = [int(max(Alist) * f) for f in (0.01, 0.05, 0.1, 0.25, 0.5, 1.0)]
    s_values   = [1.0, 1.5, 2.0, 2.5, 3.0]
    log_s_values = [1, 2]   # for 1/(a (log a)^s)

    rows = []
    header = ["threshold"]
    for s in s_values:
        header.append(f"sum_inv_a^{s}")
    for ls in log_s_values:
        header.append(f"sum_inv_a_log^{ls}")
    header.append("|A_<= threshold|")
    rows.append(header)

    for t in thresholds:
        row = [t]
        sub = [a for a in Alist if a <= t and a >= 2]
        for s in s_values:
            row.append(f"{sum(1.0 / a**s for a in sub):.6e}")
        for ls in log_s_values:
            row.append(f"{sum(1.0 / (a * math.log(a)**ls) for a in sub if math.log(a) > 0):.6e}")
        row.append(len(sub))
        rows.append(row)

    return rows


def stratify_a_n(rep, covered):
    """Running min / max of a_n / n^k, stratified."""
    ns = sorted(rep.keys())

    rows = [["n", "a_n", "a_n/n", "a_n/n^2", "a_n/n^3",
             "running_min_a_n/n^2", "running_max_a_n/n^2"]]
    rmin2, rmax2 = float("inf"), 0.0
    sample_rows = []

    log_pts = [int(10**(i/8.0)) for i in range(8, 8*4)]    # 10, ..., 10^4 logarithmically spaced
    log_pts = sorted(set(p for p in log_pts if 2 <= p <= covered))

    for n in ns:
        a = rep[n][0]
        r1 = a / n
        r2 = a / n**2
        r3 = a / n**3
        if r2 < rmin2: rmin2 = r2
        if r2 > rmax2: rmax2 = r2
        if n in log_pts or n == covered:
            sample_rows.append([n, a, f"{r1:.4f}", f"{r2:.6f}", f"{r3:.8f}",
                                f"{rmin2:.6f}", f"{rmax2:.6f}"])
    rows.extend(sample_rows)

    # Also stratify: "hard" = a_n / n^2 > 1, "easy" = a_n / n^2 <= 1.
    hard = [(n, rep[n][0]) for n in ns if rep[n][0] / n**2 > 1.0]
    easy = [(n, rep[n][0]) for n in ns if rep[n][0] / n**2 <= 1.0]

    summary = {
        "covered":   covered,
        "n_easy":    len(easy),
        "n_hard":    len(hard),
        "frac_easy": len(easy) / covered,
        "min_a_n_over_n2": min(rep[n][0] / n**2 for n in ns),
        "max_a_n_over_n2": max(rep[n][0] / n**2 for n in ns),
        "argmax_n":         max(ns, key=lambda n: rep[n][0] / n**2),
        "running_max_a_n":  max(rep[n][0] for n in ns),
    }

    # Distribution of a_n / n^2: histogram bins by powers of 2
    import collections
    hist = collections.Counter()
    for n in ns:
        v = rep[n][0] / n**2
        if v == 0:
            bin_lab = "0"
        else:
            k = int(math.floor(math.log2(v)))
            bin_lab = f"2^{k}..2^{k+1}"
        hist[bin_lab] += 1

    return rows, summary, hist, hard, easy


def main():
    ckpt_n, ckpt_path = latest_checkpoint(RESULTS)
    if ckpt_path is None:
        raise SystemExit("No checkpoint found")

    print(f"Loading checkpoint at n = {ckpt_n}: {os.path.basename(ckpt_path)}")
    with open(ckpt_path, "rb") as f:
        state = pickle.load(f)

    A       = state["A"]
    rep     = state["rep"]
    covered = state["covered"]

    print(f"  |A| = {len(A)}, covered = {covered}, max(A) = {max(A)}")

    # ── Phase 0: verification ───────────────────────────────────────────────
    print("\n" + "=" * 70)
    print(" PHASE 0  VERIFICATION")
    print("=" * 70)
    ok, report = verify(state)
    for line in report:
        print("  " + line)
    print("\n  OVERALL:", "PASS" if ok else "FAIL")

    with open(os.path.join(RESULTS, "verification_report.txt"), "w") as f:
        f.write(f"Verification of checkpoint at n = {covered}\n")
        f.write(f"|A| = {len(A)}, max(A) = {max(A)}\n\n")
        for line in report:
            f.write(line + "\n")
        f.write(f"\nOVERALL: {'PASS' if ok else 'FAIL'}\n")

    # ── Phase 1a: candidate-measure sums ────────────────────────────────────
    print("\n" + "=" * 70)
    print(" PHASE 1A  CANDIDATE MEASURE SUMS")
    print("=" * 70)
    rows = measure_sums(A, rep, covered)
    print(f"  Element-wise inverse-power sums  (s threshold = max(A) * fraction)")
    for row in rows:
        print("  " + "  ".join(str(c).rjust(14) for c in row))

    with open(os.path.join(RESULTS, "measure_sums.csv"), "w", newline="") as f:
        w = csv.writer(f); w.writerows(rows)

    # Also: the partial sum behavior as |A| grows
    Alist = sorted(A)
    print("\n  Tail sums by index:  sum_{a in A, a >= a_k} 1/a^s")
    s_vals = [1.5, 2.0, 2.5, 3.0]
    print("  " + "k".rjust(8) + "  " + "a_k".rjust(12) +
          "  " + "  ".join(f"sum 1/a^{s}".rjust(14) for s in s_vals))

    # cumulative from the END (large a)
    cum = {s: 0.0 for s in s_vals}
    sample_idx = []
    n_samples = 12
    for i in range(n_samples + 1):
        idx = max(1, int(len(Alist) * (i / n_samples)))
        sample_idx.append(idx - 1)
    sample_idx = sorted(set(sample_idx))
    rows2 = [["k", "a_k"] + [f"tail_inv_a^{s}" for s in s_vals]]
    Alist_arr = Alist
    # pre-compute tail sums efficiently
    tail = {s: [0.0] * (len(Alist_arr) + 1) for s in s_vals}
    for s in s_vals:
        run = 0.0
        for i in range(len(Alist_arr) - 1, -1, -1):
            run += 1.0 / Alist_arr[i]**s
            tail[s][i] = run
    for idx in sample_idx:
        row = [idx, Alist_arr[idx]] + [f"{tail[s][idx]:.6e}" for s in s_vals]
        rows2.append(row)
        print("  " + "  ".join(str(c).rjust(14) for c in row))

    with open(os.path.join(RESULTS, "measure_tail_sums.csv"), "w", newline="") as f:
        w = csv.writer(f); w.writerows(rows2)

    # ── Phase 1b: running min/max of a_n / n^k ──────────────────────────────
    print("\n" + "=" * 70)
    print(" PHASE 1B  STRATIFIED a_n / n^k ANALYSIS")
    print("=" * 70)
    rows_strat, summary, hist, hard, easy = stratify_a_n(rep, covered)
    print("  log-spaced samples of a_n trajectory:")
    for row in rows_strat[:1] + rows_strat[1:]:
        print("  " + "  ".join(str(c).rjust(14) for c in row))

    print("\n  Stratification summary:")
    for k, v in summary.items():
        print(f"    {k:>22}  =  {v}")

    print("\n  Histogram of a_n / n^2 by power-of-2 bins:")
    for k in sorted(hist, key=lambda s: (int(s.split('^')[1].split('..')[0]) if '^' in s else 999)):
        print(f"    {k:>16}  count = {hist[k]}")

    with open(os.path.join(RESULTS, "running_min_max.csv"), "w", newline="") as f:
        w = csv.writer(f); w.writerows(rows_strat)

    # ── Phase 1c: peaks ─────────────────────────────────────────────────────
    print("\n" + "=" * 70)
    print(" PHASE 1C  RUNNING PEAKS OF a_n / n^2")
    print("=" * 70)
    peaks = []; best = 0
    for n in sorted(rep.keys()):
        r = rep[n][0] / n**2
        if r > best:
            best = r
            peaks.append((n, rep[n][0], r))
    print(f"  Total {len(peaks)} new records of a_n / n^2 across n = 1..{covered}")
    print("  Last 25 records:")
    print("  " + "n".rjust(7) + "  " + "a_n".rjust(14) + "  " +
          "a_n/n^2".rjust(12) + "  " + "a_n/(n^2 ln n)".rjust(16) + "  " +
          "a_n/n^3".rjust(14))
    for n, a, r in peaks[-25:]:
        print(f"  {n:>7}  {a:>14}  {r:>12.4f}  {a/(n**2*math.log(max(n,2))):>16.6f}  {a/n**3:>14.8f}")

    # log-log fit on the peaks tail
    if len(peaks) >= 8:
        tail = peaks[-30:] if len(peaks) >= 30 else peaks
        log_n = [math.log(p[0]) for p in tail]
        log_a = [math.log(p[1]) for p in tail]
        k = len(tail)
        slope = (k*sum(x*y for x,y in zip(log_n,log_a)) - sum(log_n)*sum(log_a)) / \
                (k*sum(x**2 for x in log_n) - sum(log_n)**2)
        inter = (sum(log_a) - slope*sum(log_n)) / k
        print(f"\n  Log-log fit (last {k} peaks):  a_n ~ {math.exp(inter):.4f} * n^{slope:.4f}")

    with open(os.path.join(RESULTS, "peaks.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["n", "a_n", "a_n_over_n2"])
        for p in peaks:
            w.writerow([p[0], p[1], f"{p[2]:.6f}"])

    print("\n" + "=" * 70)
    print(" DONE.  Outputs in:", RESULTS)
    print("=" * 70)


if __name__ == "__main__":
    main()
