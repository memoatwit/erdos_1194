#!/usr/bin/env python3
"""Independently audit the high-level r_3(N) constraint generator.

The audit uses only the Python standard library and does not import the solver
implementation. It emits counts and SHA-256 digests for the AP triples, the
OEIS-derived window inequalities, and the complete high-level decision model.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for block in iter(lambda: fh.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def load_bfile(path: Path) -> dict[int, int]:
    values: dict[int, int] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        n_text, value_text = line.split()[:2]
        n = int(n_text)
        value = int(value_text)
        if n in values:
            raise ValueError(f"duplicate b-file index {n}")
        values[n] = value
    return values


def update_line(digest: hashlib._Hash, *parts: object) -> None:  # type: ignore[name-defined]
    digest.update((" ".join(str(part) for part in parts) + "\n").encode("ascii"))


def audit(N: int, K: int, bfile: Path, force_endpoints: list[int]) -> dict:
    values = load_bfile(bfile)
    indices = sorted(values)
    if indices != list(range(indices[0], indices[-1] + 1)):
        raise ValueError("b-file indices are not contiguous")
    for n in indices[1:]:
        if values[n] < values[n - 1] or values[n] > values[n - 1] + 1:
            raise ValueError(f"invalid r_3 increment at n={n}")

    ap_digest = hashlib.sha256()
    full_digest = hashlib.sha256()
    ap_count = 0
    for middle in range(1, N + 1):
        for difference in range(1, min(middle - 1, N - middle) + 1):
            triple = (middle - difference, middle, middle + difference)
            update_line(ap_digest, "AP", *triple)
            update_line(full_digest, "AP", *triple)
            ap_count += 1

    window_digest = hashlib.sha256()
    window_count = 0
    active_lengths = []
    rhs_histogram: dict[int, int] = {}
    for length in range(2, N + 1):
        rhs = values.get(length)
        if rhs is None or rhs >= length or rhs >= K:
            continue
        active_lengths.append(length)
        rhs_histogram[rhs] = rhs_histogram.get(rhs, 0) + (N - length + 1)
        for start in range(1, N - length + 2):
            update_line(window_digest, "WINDOW", start, length, rhs)
            update_line(full_digest, "WINDOW", start, length, rhs)
            window_count += 1

    update_line(full_digest, "CARDINALITY_EQ", K)
    for endpoint in sorted(force_endpoints):
        update_line(full_digest, "FIX_IN", endpoint)
    update_line(full_digest, "REFLECTION_LEX_GE", 1, N)

    return {
        "audit": "independent-high-level-model-generator",
        "N": N,
        "K": K,
        "bfile": bfile.name,
        "bfile_sha256": sha256_file(bfile),
        "bfile_first_index": indices[0],
        "bfile_last_index": indices[-1],
        "bfile_entries": len(indices),
        "bfile_monotone_unit_increments": True,
        "ap_constraints": ap_count,
        "ap_constraints_sha256": ap_digest.hexdigest(),
        "window_filter": "r3(L) < min(L,K)",
        "window_constraints": window_count,
        "window_constraints_sha256": window_digest.hexdigest(),
        "active_window_length_count": len(active_lengths),
        "active_window_length_min": min(active_lengths),
        "active_window_length_max": max(active_lengths),
        "active_window_lengths": active_lengths,
        "window_rhs_constraint_histogram": {
            str(rhs): count for rhs, count in sorted(rhs_histogram.items())
        },
        "force_endpoints": sorted(force_endpoints),
        "reflection_constraint": "x[1..N] lexicographically >= reverse(x[1..N])",
        "high_level_model_sha256": full_digest.hexdigest(),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--N", type=int, default=212)
    parser.add_argument("--K", type=int, default=44)
    parser.add_argument(
        "--bfile",
        type=Path,
        default=Path(__file__).resolve().parent / "results/b003002.txt",
    )
    parser.add_argument("--force-endpoints", type=int, nargs="*", default=[1, 212])
    parser.add_argument(
        "--output",
        type=Path,
        default=Path(__file__).resolve().parent / "results/N212_K44_model_audit.json",
    )
    args = parser.parse_args()

    result = audit(args.N, args.K, args.bfile, args.force_endpoints)
    if args.N == 212 and args.K == 44:
        if result["ap_constraints"] != 11_130:
            raise SystemExit("unexpected AP constraint count")
        if result["window_constraints"] != 22_154:
            raise SystemExit("unexpected window constraint count")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
