"""
Phase 6 — block-structured PDS constructions.

Tests several strategies for breaking the Θ(N³) ceiling:

1. Single-block seeding with varying seed sizes (extends Phase 3').
2. Double-block: A = MC(k) ∪ (MC(k) + c) for chosen shift c.
3. Triple-block / multi-block with arithmetic-progression-like offsets.
4. Greedy continuation from each variant; compare max(A)/N^c growth.

Usage:
  python3 block_construction.py mc 200 800        # single MC seed of size 200, target N=800
  python3 block_construction.py double 60 800     # double MC of size 60, target N=800
  python3 block_construction.py sweep             # sweep all strategies, summary table
"""
from __future__ import annotations
import os, sys, csv, math, time, json
from seeded_greedy import mian_chowla, seeded_greedy

THIS_DIR = os.path.dirname(os.path.abspath(__file__))
RESULTS  = os.path.join(THIS_DIR, "results")


def verify_sidon(A: list[int]) -> tuple[bool, int]:
    """Returns (is_sidon, smallest duplicate difference or -1)."""
    diffs = {}
    A_s = sorted(A)
    for i in range(len(A_s)):
        for j in range(i):
            d = A_s[i] - A_s[j]
            if d in diffs:
                return False, d
            diffs[d] = (A_s[j], A_s[i])
    return True, -1


def split_mc_block(k1: int, k2: int, gap: int | None = None) -> list[int]:
    """Build A from the FIRST k1 elements of Mian-Chowla, plus a separate copy
    of MC elements indexed (k1+1..k1+k2) shifted by 'gap'. Result is two
    disjoint Mian-Chowla sub-blocks. They share NO within-block differences
    because MC is globally Sidon, so as long as cross-block differences
    don't collide, the union is Sidon.

    Auto-shift: pick gap large enough that all cross-block differences are
    strictly greater than max within-block difference.
    """
    mc = mian_chowla(k1 + k2)
    B1 = mc[:k1]
    B2 = mc[k1:k1+k2]
    # within-block diffs
    within = set()
    for i in range(len(B1)):
        for j in range(i):
            within.add(B1[i] - B1[j])
    for i in range(len(B2)):
        for j in range(i):
            within.add(B2[i] - B2[j])
    # We want gap large enough that cross diffs avoid within diffs.
    # Cross diffs = (B2 + gap) - B1 = (B2 - B1) + gap. For these to avoid
    # the within set, choose gap > max(within) + max(B1) so all cross diffs
    # exceed max(within).
    if gap is None:
        gap = max(within) + max(B1) + 1
    A = sorted(set(B1) | set(x + gap for x in B2))
    return A


def mc_arithmetic_progression(k: int, m: int, spacing: int | None = None) -> list[int]:
    """A = union over j in [0, m) of (MC_chunk_j + j * spacing).

    Each MC_chunk_j is the k Mian-Chowla elements at indices [j*k, (j+1)*k).
    spacing is chosen so cross-chunk diffs exceed within-chunk diffs."""
    mc = mian_chowla(k * m)
    chunks = [mc[j*k:(j+1)*k] for j in range(m)]
    within_max = 0
    for chunk in chunks:
        for i in range(len(chunk)):
            for j in range(i):
                within_max = max(within_max, chunk[i] - chunk[j])
    if spacing is None:
        # Generous: spacing > within_max + max element value
        spacing = within_max + max(mc) + 1
    A = set()
    for j, chunk in enumerate(chunks):
        A |= set(x + j * spacing for x in chunk)
    return sorted(A)


def run_strategy(name: str, A_seed: list[int], target_N: int,
                 verbose: bool = False) -> dict:
    """Run seeded greedy and return summary."""
    print(f"\n  === {name}: |seed|={len(A_seed)}, max(seed)={max(A_seed)} ===",
          flush=True)
    ok, dup = verify_sidon(A_seed)
    if not ok:
        return {"name": name, "error": f"seed not Sidon (dup={dup})"}
    t0 = time.time()
    try:
        A, rep, s2 = seeded_greedy(A_seed, target_N, verbose=False)
        elapsed = time.time() - t0
        max_A = max(A)
        # Stratify a_n
        N_actual = max(rep.keys())
        peak = max(rep[n][0] for n in rep)
        return {
            "name": name, "seed_size": len(A_seed), "seed_max": max(A_seed),
            "N": N_actual, "max_A": max_A, "|A|": len(A),
            "strat2_count": s2, "ratio_n3": max_A / N_actual**3,
            "elapsed_s": elapsed,
        }
    except Exception as e:
        return {"name": name, "error": str(e), "elapsed_s": time.time() - t0}


def sweep(target_N: int = 500, mc_sizes: list[int] = None) -> list[dict]:
    """Run a sweep of strategies at given target N."""
    if mc_sizes is None:
        mc_sizes = [30, 60, 100, 150, 200]
    results = []
    # Single MC seed sweep
    for k in mc_sizes:
        seed = mian_chowla(k)
        results.append(run_strategy(f"MC({k})", seed, target_N))
    # Split MC sweep (two disjoint MC chunks)
    for (k1, k2) in [(30, 30), (40, 40), (60, 30)]:
        seed = split_mc_block(k1, k2)
        if max(seed) < 1_000_000:
            results.append(run_strategy(f"split_MC({k1},{k2})", seed, target_N))
    # Arithmetic-progression chunks
    for (k, m) in [(20, 3), (30, 2)]:
        seed = mc_arithmetic_progression(k, m)
        if max(seed) < 1_000_000:
            results.append(run_strategy(f"AP_MC(k={k},m={m})", seed, target_N))
    return results


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    mode = sys.argv[1]
    if mode == "mc":
        k = int(sys.argv[2]); N = int(sys.argv[3])
        seed = mian_chowla(k)
        result = run_strategy(f"MC({k})", seed, N)
        print(json.dumps(result, indent=2))
    elif mode == "split":
        k1 = int(sys.argv[2]); k2 = int(sys.argv[3]); N = int(sys.argv[4])
        seed = split_mc_block(k1, k2)
        result = run_strategy(f"split_MC({k1},{k2})", seed, N)
        print(json.dumps(result, indent=2))
    elif mode == "ap":
        k = int(sys.argv[2]); m = int(sys.argv[3]); N = int(sys.argv[4])
        seed = mc_arithmetic_progression(k, m)
        result = run_strategy(f"AP_MC(k={k},m={m})", seed, N)
        print(json.dumps(result, indent=2))
    elif mode == "sweep":
        N = int(sys.argv[2]) if len(sys.argv) > 2 else 500
        mc_sizes = [int(x) for x in sys.argv[3:]] if len(sys.argv) > 3 else None
        results = sweep(target_N=N, mc_sizes=mc_sizes)
        # Save
        out = os.path.join(RESULTS, f"block_sweep_N{N}.json")
        with open(out, "w") as f:
            json.dump(results, f, indent=2, default=str)
        print(f"\nSaved → {out}")
        # Summary
        print(f"\n{'Strategy':<20} {'|seed|':>8} {'seed_max':>10} "
              f"{'max(A)':>10} {'ratio/N³':>10} {'|A|':>5} {'s2':>5} {'t(s)':>6}")
        for r in results:
            if "error" in r:
                print(f"{r['name']:<20} ERROR: {r['error']}")
                continue
            print(f"{r['name']:<20} {r['seed_size']:>8} {r['seed_max']:>10} "
                  f"{r['max_A']:>10} {r['ratio_n3']:>10.5f} "
                  f"{r['|A|']:>5} {r['strat2_count']:>5} {r['elapsed_s']:>6.1f}")
    else:
        print(f"Unknown mode: {mode}")
        sys.exit(1)


if __name__ == "__main__":
    main()
