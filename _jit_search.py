"""
Numba JIT inner loop for Erdős #1194 Strategy 2 scan.
Must live in a real .py file (not inline) so numba can cache compilation.
"""
import numba as nb
import numpy as np


@nb.njit(cache=True)
def find_valid_b(A_arr, diffs_bool, n, max_A, covered, max_scan):
    """
    Find the smallest b > max_A + covered such that adding (b, b+n) to the PDS
    is valid (no difference collisions).

    Rules checked for each candidate b:
      1. b - x  ∉ diffs  for all x ∈ A_arr  (b-x > 0 since b > max_A ≥ x)
      2. b + n - x  ∉ diffs  for all x ∈ A_arr
      3. b - x ≠ n  for all x ∈ A_arr  (i.e. b ≠ x+n, prevents n appearing twice)

    Returns the first valid b, or -1 if none found within max_scan of max_A.
    """
    max_diff = len(diffs_bool) - 2
    # Skip b values where b - max_A <= covered, since those fail Rule 1
    # immediately (max_A ∈ A, b - max_A ≤ covered means that diff is taken).
    b = max_A + covered + 1
    limit = max_A + max_scan

    while b <= limit:
        valid = True
        for i in range(len(A_arr)):
            x = A_arr[i]
            d1 = b - x          # always > 0
            # Rule 3: b - x == n means b = x+n, difference n would collide
            if d1 == n:
                valid = False
                break
            # Rule 1
            if d1 <= max_diff and diffs_bool[d1]:
                valid = False
                break
            # Rule 2
            d2 = d1 + n         # (b+n) - x
            if d2 <= max_diff and diffs_bool[d2]:
                valid = False
                break
        if valid:
            return b
        b += 1
    return -1
