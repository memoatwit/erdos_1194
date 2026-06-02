"""
Phase 2B — Fourier-side observable probes.

For greedy PDS A_N (read from results/pds_*.csv or checkpoints), compute:

1. L^p norms of the indicator's Fourier transform:
   ||1_A^hat||_p^p = integral_0^1 |1_A^hat(xi)|^p dxi.
   - p=2: |A| (Plancherel).
   - p=4: |A|^2 + 2 * binom(|A|, 2) = 2|A|^2 - |A|  (Sidon, no extra info).
   - p=6 and higher: meaningful only if differences have nontrivial structure;
     for a true Sidon set these are determined.

2. Fejer-kernel inner product at width T:
   IF [1, T] subset (A - A), then
   integral K_T |1_A^hat|^2 = |A| + 2 sum_{n=1}^{T-1} (1 - n/T)
                            = |A| + (T - 1).
   Easy to verify numerically.

3. Anchor-window density: for each k, |A intersect [x_k - X, x_k)| at
   chosen X.  Phase 2C Step 3 bounds this by X / x_k^(1/c) for c = 2.
   We measure the actual density vs the bound to see slack.

4. Consecutive-gap distribution: histograms of d_k = x_k - x_{k-1}
   vs k, and vs sqrt(x_k).

These do not prove anything new; they look for slack in the Step 3
estimate that could break the c = 2 ceiling.

Usage:
  python3 fourier_probes.py 200
  python3 fourier_probes.py 1000 1500
"""
from __future__ import annotations
import os, sys, csv, math, json, pickle
import numpy as np

THIS_DIR = os.path.dirname(os.path.abspath(__file__))
RESULTS  = os.path.join(THIS_DIR, "results")


def load_greedy_A(N: int) -> list[int]:
    """Load A from the largest checkpoint or CSV up to step N."""
    # Try CSV first
    csv_path = os.path.join(RESULTS, f"pds_{N}.csv")
    if os.path.exists(csv_path):
        A = set()
        with open(csv_path) as f:
            r = csv.DictReader(f)
            for row in r:
                if int(row["n"]) <= N:
                    A.add(int(row["a_n"]))
                    A.add(int(row["b_n"]))
        return sorted(A)
    # Fall back to checkpoint
    for ckpt_n in sorted([int(f[len("checkpoint_"):-4])
                          for f in os.listdir(RESULTS)
                          if f.startswith("checkpoint_") and f.endswith(".pkl")
                          ], reverse=True):
        if ckpt_n >= N:
            try:
                state = pickle.load(open(os.path.join(RESULTS, f"checkpoint_{ckpt_n}.pkl"), "rb"))
                # Pull elements with rep up to N
                A = set()
                for n in range(1, N + 1):
                    if n in state["rep"]:
                        a, b = state["rep"][n]
                        A.add(a); A.add(b)
                return sorted(A)
            except Exception:
                continue
    raise FileNotFoundError(f"No greedy data for N={N}")


def fourier_norms(A: list[int], grid_size: int = None) -> dict:
    """Compute L^p norms of |1_A^hat|^p on a uniform grid of [0, 1)."""
    M = max(A)
    if grid_size is None:
        grid_size = 8 * M       # 8x oversample
    # FFT: f[k] = sum_{a in A} exp(-2 pi i a k / grid_size)
    indicator = np.zeros(grid_size, dtype=np.complex128)
    for a in A:
        indicator[a % grid_size] += 1
    fhat = np.fft.fft(indicator)
    mag2 = np.abs(fhat)**2
    norms = {}
    for p in (2, 4, 6, 8):
        norms[f"L{p}"] = float((mag2**(p/2)).mean())
    # Sanity: L^2 should equal |A|
    norms["sanity_L2_vs_|A|"] = (norms["L2"], len(A))
    return norms


def fejer_inner_product(A: list[int], T: int, grid_size: int = None) -> dict:
    """Numerically compute integral K_T(xi) |1_A^hat(xi)|^2 dxi.

    For T <= T_max where [1, T_max] subset (A - A), the value should be
    |A| + (T - 1).  We test this identity.
    """
    M = max(A)
    if grid_size is None:
        grid_size = 8 * M
    indicator = np.zeros(grid_size, dtype=np.complex128)
    for a in A:
        indicator[a % grid_size] += 1
    fhat = np.fft.fft(indicator)
    mag2 = np.abs(fhat)**2
    # K_T(xi) = sum_{|n| < T} (1 - |n|/T) e^{2 pi i n xi}
    # On the grid xi_k = k / grid_size:
    kt = np.zeros(grid_size, dtype=np.float64)
    for n in range(-(T-1), T):
        kt[n % grid_size] += (1 - abs(n)/T)
    # Inner product (Parseval style): integral K_T |fhat|^2 = sum_k K_T_hat[k] * mag2[k] / grid_size... hmm.
    # Better: do it in physical space using convolution.
    # integral K_T |fhat|^2 dxi = sum_n K_T_coeffs(n) * conv(n) where conv = 1_A * 1_A^-
    # where conv(n) = #{(a, b) in A^2: a - b = n}.
    # K_T_coeffs(n) = (1 - |n|/T) if |n| < T else 0.
    # So integral = sum_{|n| < T} (1 - |n|/T) conv(n)
    #             = |A| * 1                                  (n=0)
    #             + 2 sum_{n=1}^{T-1} (1 - n/T) conv(n)
    A_set = set(A)
    val = float(len(A))     # n = 0 contributes (1 - 0) * |A|
    for n in range(1, T):
        c = sum(1 for a in A if (a - n) in A_set)
        val += 2 * (1 - n/T) * c
    # The predicted PDS value (if [1, T-1] all in A - A): |A| + (T - 1).
    # Actually with the 2 sum factor:
    # if conv(n) = 1 for all n in [1, T-1], sum = sum_{n=1}^{T-1} (1 - n/T) = (T-1)/2
    # so 2 * (T-1)/2 = T - 1.
    predicted_if_covered = len(A) + (T - 1)
    return {"T": T, "fejer_inner_product": val,
            "predicted_if_covered": predicted_if_covered,
            "matches": abs(val - predicted_if_covered) < 1e-9}


def anchor_window_density(A: list[int], X: int) -> dict:
    """For each k, compute |A intersect [x_k - X, x_k)| and compare to
    Phase 2C Step 3 bound X / sqrt(x_k).
    """
    A_sorted = sorted(A)
    M = max(A)
    rows = []
    for k_idx, xk in enumerate(A_sorted):
        if xk <= 2 * X:
            continue
        lo = xk - X
        # Count elements in [lo, xk).  Use binary search.
        import bisect
        L = bisect.bisect_left(A_sorted, lo)
        R = bisect.bisect_left(A_sorted, xk)
        count = R - L
        bound = X / math.sqrt(xk)
        rows.append({"k": k_idx + 1, "x_k": xk, "count": count,
                     "bound_X/sqrt(xk)": bound,
                     "ratio_count/bound": count / bound if bound > 0 else 0.0})
    return rows


def gap_stats(A: list[int]) -> dict:
    """Statistics of consecutive gaps d_k vs k and x_k."""
    A_sorted = sorted(A)
    gaps = [A_sorted[i] - A_sorted[i-1] for i in range(1, len(A_sorted))]
    # Predicted by Phase 2C/5: d_k ~ x_k^{1/c} or d_k ~ sqrt(x_k * f(x_k))
    # Compute log slopes.
    log_k = np.log(np.arange(2, len(A_sorted) + 1))
    log_d = np.log(np.array(gaps))
    log_x = np.log(np.array(A_sorted[1:]))
    slope_d_k, _ = np.polyfit(log_k, log_d, 1)
    slope_d_x, _ = np.polyfit(log_x, log_d, 1)
    return {
        "|A|": len(A_sorted),
        "min_gap": min(gaps),
        "max_gap": max(gaps),
        "median_gap": int(sorted(gaps)[len(gaps)//2]),
        "log_slope_d_vs_k":  float(slope_d_k),
        "log_slope_d_vs_x":  float(slope_d_x),
    }


def main(Ns):
    for N in Ns:
        print("=" * 70)
        print(f" Phase 2B Fourier probes — greedy A at N = {N}")
        print("=" * 70)
        A = load_greedy_A(N)
        print(f"  |A| = {len(A)},  max(A) = {max(A):,}")

        # Gap stats (cheap)
        gs = gap_stats(A)
        print(f"\n  Gap statistics:")
        for k, v in gs.items():
            print(f"    {k:>22}  = {v}")

        # Fejer identity check at T = N (where coverage is exact for greedy)
        # Only do this for moderate N (cost is O(|A| * T) for the explicit sum)
        if N <= 500:
            print(f"\n  Fejér inner product at T={min(N, 100)} (PDS identity test):")
            T_test = min(N, 100)
            fj = fejer_inner_product(A, T_test)
            print(f"    {fj}")

        # Anchor window densities at several X values
        print(f"\n  Anchor window densities (Phase 2C Step 3 slack):")
        for X in (max(A) // 20, max(A) // 10, max(A) // 4):
            rows = anchor_window_density(A, X)
            if not rows:
                continue
            counts = [r["count"] for r in rows]
            ratios = [r["ratio_count/bound"] for r in rows]
            ratios_arr = np.array(ratios)
            print(f"    X = {X:,}: {len(rows)} anchors with x_k > 2X")
            print(f"      median count = {sorted(counts)[len(counts)//2]}")
            print(f"      median ratio count / (X/sqrt(xk)) = {float(np.median(ratios_arr)):.4f}")
            print(f"      max ratio                          = {ratios_arr.max():.4f}")

        # Save full anchor-window data for the largest X
        out_anchor = os.path.join(RESULTS, f"fourier_anchor_N{N}.json")
        rows_all = anchor_window_density(A, max(A) // 10)
        with open(out_anchor, "w") as f:
            json.dump(rows_all, f, indent=2, default=str)


if __name__ == "__main__":
    Ns = [int(a) for a in sys.argv[1:]] or [500]
    main(Ns)
