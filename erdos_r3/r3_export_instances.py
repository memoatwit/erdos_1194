#!/usr/bin/env python3
"""
r3_export_instances.py — export r_3(N, K) benchmark instances in standard formats.

Produces, for each chunk (or for the monolithic unsplit instance):
  * DIMACS CNF   (same encoding as r3_sat_attack.py: 3-AP binary clauses,
                  sequential-counter window at-most-k, totalizer sum = K,
                  endpoint forcing, chunk pins as unit clauses)
  * MiniZinc     (declarative model; windows and cardinality stay as
                  integer constraints, no encoding artifacts)

Usage:
  # Export the T1c pair in both formats:
  python3 r3_export_instances.py --jsonl results/N212_K44_t1c2.jsonl --outdir export/

  # Export all tiers:
  for f in results/N212_K44_t1a25.jsonl results/N212_K44_t1b_minus_t1c.jsonl \
           results/N212_K44_t1c2.jsonl; do
    python3 r3_export_instances.py --jsonl "$f" --outdir export/
  done

  # Export the monolithic (unsplit) instance, with and without windows:
  python3 r3_export_instances.py --monolithic --outdir export/
  python3 r3_export_instances.py --monolithic --no-windows --outdir export/

Dependencies: python-sat (only for CNF export; MiniZinc export is pure Python).
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from r3_sat_attack import (
    build_window_constraints,
    encode_chunk_as_cnf,
    enumerate_3ap_triples,
    load_window_bounds,
)


def export_cnf(
    out: Path,
    N: int,
    K: int,
    fixed_in: list[int],
    fixed_out: list[int],
    windows: list[tuple[list[int], int]],
    label: str,
) -> dict:
    triples = enumerate_3ap_triples(N)
    cnf, stats = encode_chunk_as_cnf(
        N, K, fixed_in, fixed_out, triples, windows, force_endpoints=True
    )
    enc_desc = (
        "3-AP binary clauses; window at-most-k (seqcounter); sum = K (totalizer)"
        if windows
        else "3-AP binary clauses; sum = K (totalizer)"
    )
    cnf.comments = [
        f"c r_3({N}) <= {K - 1} decision instance: {label}",
        f"c vars 1..{N} = membership of i in A subset [1, {N}]",
        f"c SAT <=> a {K}-element 3-AP-free subset exists under the pins",
        f"c pins: fixed_in={fixed_in} fixed_out={fixed_out}",
        f"c encoding: {enc_desc};",
        f"c           endpoint forcing x_1 = x_{N} = 1",
        "c source: github.com/memoatwit/erdos_1194 (erdos_r3), CC-BY",
    ]
    cnf.to_file(str(out))
    return stats


def export_minizinc(
    out: Path,
    N: int,
    K: int,
    fixed_in: list[int],
    fixed_out: list[int],
    r3_table: dict[int, int] | None,
    label: str,
) -> None:
    lines = [
        f"% r_3({N}) <= {K - 1} decision instance: {label}",
        f"% SATISFIABLE <=> a {K}-element 3-AP-free subset of [1, {N}] exists",
        "% source: github.com/memoatwit/erdos_1194 (erdos_r3), CC-BY",
        f"int: N = {N};",
        f"int: K = {K};",
        "array[1..N] of var 0..1: x;",
        "",
        "% no 3-term arithmetic progression",
        "constraint forall(a in 1..N, d in 1..((N - a) div 2))(",
        "  x[a] + x[a + d] + x[a + 2 * d] <= 2);",
        "",
        "% cardinality target",
        "constraint sum(x) = K;",
        "",
        "% endpoint forcing (valid because r_3(N - 1) = K - 1)",
        "constraint x[1] = 1 /\\ x[N] = 1;",
    ]
    if r3_table:
        useful = sorted(
            (L, k) for L, k in r3_table.items() if 3 <= L <= N and k < min(L, K)
        )
        Ls = ", ".join(str(L) for L, _ in useful)
        ks = ", ".join(str(k) for _, k in useful)
        lines += [
            "",
            "% window-cardinality implied constraints from known r_3(L) values",
            f"array[int] of int: winL = [{Ls}];",
            f"array[int] of int: winK = [{ks}];",
            "constraint forall(j in index_set(winL), a in 1..(N - winL[j] + 1))(",
            "  sum(i in a..(a + winL[j] - 1))(x[i]) <= winK[j]);",
        ]
    if fixed_in:
        lines += ["", "% chunk pins (IN)"] + [
            f"constraint x[{v}] = 1;" for v in fixed_in
        ]
    if fixed_out:
        lines += ["", "% chunk pins (OUT)"] + [
            f"constraint x[{v}] = 0;" for v in fixed_out
        ]
    lines += ["", "solve satisfy;", 'output ["A = ", show([i | i in 1..N where fix(x[i]) = 1])];']
    out.write_text("\n".join(lines) + "\n")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--jsonl", type=Path, help="chunk JSONL to export")
    ap.add_argument("--monolithic", action="store_true", help="export unsplit instance")
    ap.add_argument("--no-windows", action="store_true", help="omit window bounds")
    ap.add_argument("--outdir", type=Path, default=Path("export"))
    ap.add_argument("--b-file", type=Path, default=Path("results/b003002.txt"))
    ap.add_argument("--N", type=int, default=212)
    ap.add_argument("--K", type=int, default=44)
    args = ap.parse_args()

    args.outdir.mkdir(parents=True, exist_ok=True)
    r3_table = None if args.no_windows else load_window_bounds(args.b_file)
    windows = (
        []
        if args.no_windows
        else build_window_constraints(args.N, args.K, r3_table)
    )
    suffix = "nowin" if args.no_windows else "win"

    jobs: list[tuple[str, list[int], list[int]]] = []
    if args.monolithic:
        jobs.append((f"N{args.N}_K{args.K}_monolithic_{suffix}", [], []))
    if args.jsonl:
        tier = args.jsonl.stem
        for line in args.jsonl.open():
            row = json.loads(line)
            jobs.append(
                (
                    f"{tier}_chunk{row['chunk_id']}_{suffix}",
                    sorted(set(row.get("fixed_in", []))),
                    sorted(set(row.get("fixed_out", []))),
                )
            )
    if not jobs:
        ap.error("nothing to export: pass --jsonl and/or --monolithic")

    for label, fin, fout in jobs:
        cnf_path = args.outdir / f"{label}.cnf"
        mzn_path = args.outdir / f"{label}.mzn"
        stats = export_cnf(cnf_path, args.N, args.K, fin, fout, windows, label)
        export_minizinc(mzn_path, args.N, args.K, fin, fout, r3_table, label)
        print(
            f"{label}: {cnf_path} ({stats['n_vars']} vars, "
            f"{stats['n_clauses']} clauses); {mzn_path}"
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
