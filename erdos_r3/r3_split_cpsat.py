"""
Split CP-SAT runner for fixed-cardinality r_3(N) decision proofs.

This runs the decision problem "is there a K-point 3-AP-free subset of [1..N]?"
across deterministic chunks defined by assignments to reflected endpoint pairs

  (1,N), (2,N-1), ...

Each chunk fixes those variables and calls r3_cpsat.solve_r3_cpsat with
sum(x) == K.  Results are appended as JSONL and the runner is resumable by
skipping chunk_ids already present in the output file.  If endpoint pairs do
not split the hard core well, use `--strategy degree-vars` to split on variables
that occur in the most 3-AP constraints.

Usage:
  python3 erdos_r3/r3_split_cpsat.py --N 212 --K 44 --pairs 10 \
    --chunk-time-limit 600 --workers-per-chunk 8 \
    --hint erdos_r3/results/N212_K43_witness.json \
    --output erdos_r3/results/N212_K44_split_pairs10.jsonl
"""
from __future__ import annotations

import argparse
import json
import time
from pathlib import Path
from typing import Iterator

from r3_cpsat import arithmetic_progressions, load_int_set, load_window_bounds, solve_r3_cpsat
from r3_verify import verify


PAIR_VALUES = ((0, 0), (1, 0), (1, 1), (0, 1))


def existing_chunk_ids(path: Path) -> set[int]:
    if not path.exists():
        return set()
    out = set()
    with path.open("r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            if "chunk_id" in row:
                out.add(int(row["chunk_id"]))
    return out


def load_jsonl_chunk(path: Path, chunk_id: int) -> dict:
    with path.open("r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            row = json.loads(line)
            if int(row.get("chunk_id", -1)) == chunk_id:
                return row
    raise ValueError(f"chunk_id {chunk_id} not found in {path}")


def prefix_assignments(N: int, pairs: int) -> Iterator[dict]:
    """Yield lex-valid reflected-pair assignments with stable chunk IDs."""
    pair_list = [(i, N + 1 - i) for i in range(1, pairs + 1)]
    chunk_id = 0

    def rec(index: int, relation: str, fixed_in: list[int], fixed_out: list[int], prefix: list[dict]):
        nonlocal chunk_id
        if index == len(pair_list):
            yield {
                "chunk_id": chunk_id,
                "fixed_in": sorted(fixed_in),
                "fixed_out": sorted(fixed_out),
                "prefix": list(prefix),
            }
            chunk_id += 1
            return

        left, right = pair_list[index]
        for left_value, right_value in PAIR_VALUES:
            if relation == "equal" and left_value < right_value:
                continue
            next_relation = relation
            if relation == "equal" and left_value > right_value:
                next_relation = "greater"
            next_in = list(fixed_in)
            next_out = list(fixed_out)
            (next_in if left_value else next_out).append(left)
            (next_in if right_value else next_out).append(right)
            next_prefix = list(prefix)
            next_prefix.append({
                "left": left,
                "right": right,
                "left_value": left_value,
                "right_value": right_value,
            })
            yield from rec(index + 1, next_relation, next_in, next_out, next_prefix)

    yield from rec(0, "equal", [], [], [])


def degree_split_variables(N: int, count: int) -> list[int]:
    degrees = {i: 0 for i in range(1, N + 1)}
    for triple in arithmetic_progressions(N):
        for value in triple:
            degrees[value] += 1
    center = (N + 1) / 2
    ranked = sorted(range(1, N + 1), key=lambda value: (-degrees[value], abs(value - center), value))
    return ranked[:count]


def variable_assignments(
    N: int,
    variables: list[int],
    *,
    prune_prefix_ap: bool = False,
    prune_base_in: list[int] | None = None,
) -> Iterator[dict]:
    chunk_id = 0
    base_in = prune_base_in or []

    def rec(index: int, fixed_in: list[int], fixed_out: list[int], prefix: list[dict]):
        nonlocal chunk_id
        if index == len(variables):
            yield {
                "chunk_id": chunk_id,
                "fixed_in": sorted(fixed_in),
                "fixed_out": sorted(fixed_out),
                "prefix": list(prefix),
            }
            chunk_id += 1
            return
        value = variables[index]
        # Try selected-first.  High-incidence selected prefixes often become
        # AP-incompatible quickly, so this produces early logged progress.
        for bit in (1, 0):
            next_in = list(fixed_in)
            next_out = list(fixed_out)
            (next_in if bit else next_out).append(value)
            if prune_prefix_ap and bit and not verify([*base_in, *next_in], N=N).get("ok"):
                continue
            next_prefix = list(prefix)
            next_prefix.append({"value": value, "selected": bit})
            yield from rec(index + 1, next_in, next_out, next_prefix)

    yield from rec(0, [], [], [])


def skip_reason(N: int, K: int, fixed_in: list[int], fixed_out: list[int]) -> str | None:
    if len(fixed_in) > K:
        return "SKIPPED_TOO_MANY_FIXED_IN"
    remaining_free = N - len(fixed_in) - len(fixed_out)
    if len(fixed_in) + remaining_free < K:
        return "SKIPPED_CARDINALITY"
    report = verify(fixed_in, N=N)
    if not report.get("ok"):
        return "SKIPPED_PREFIX_AP"
    return None


def merge_fixed(global_values: list[int], chunk_values: list[int]) -> list[int]:
    return sorted(set(global_values) | set(chunk_values))


def summarize_jsonl(path: Path) -> dict:
    counts: dict[str, int] = {}
    hardest = []
    if not path.exists():
        return {"counts": counts, "hardest": hardest}
    with path.open("r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            row = json.loads(line)
            status = row.get("status", "UNKNOWN")
            counts[status] = counts.get(status, 0) + 1
            if status in {"UNKNOWN", "INFEASIBLE"}:
                hardest.append({
                    "chunk_id": row.get("chunk_id"),
                    "status": status,
                    "seconds": row.get("seconds", 0),
                    "branches": row.get("branches", 0),
                    "conflicts": row.get("conflicts", 0),
                })
    hardest.sort(key=lambda row: (row["seconds"], row["branches"], row["conflicts"]), reverse=True)
    return {"counts": counts, "hardest": hardest[:10]}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--N", type=int, required=True)
    parser.add_argument("--K", type=int, required=True)
    parser.add_argument("--pairs", type=int, required=True)
    parser.add_argument("--strategy", choices=["endpoint-pairs", "degree-vars"], default="endpoint-pairs")
    parser.add_argument("--split-count", type=int, default=None,
                        help="number of reflected pairs or degree-ranked variables to split")
    parser.add_argument("--chunk-time-limit", type=float, default=600)
    parser.add_argument("--workers-per-chunk", type=int, default=8)
    parser.add_argument("--hint", type=Path, default=None)
    parser.add_argument("--fix-in", type=Path, default=None,
                        help="JSON list/dict of elements forced into every chunk")
    parser.add_argument("--fix-out", type=Path, default=None,
                        help="JSON list/dict of elements forced out of every chunk")
    parser.add_argument("--branch-order", choices=["natural", "degree", "reverse-degree"], default="natural")
    parser.add_argument("--branch-value", choices=["max", "min"], default="max")
    parser.add_argument("--fixed-search", action="store_true")
    parser.add_argument("--split-vars", type=Path, default=None,
                        help="optional JSON list/dict of explicit variables for degree-vars splitting")
    parser.add_argument("--base-jsonl", type=Path, default=None,
                        help="JSONL output from a prior split run containing the chunk to refine")
    parser.add_argument("--base-chunk-id", type=int, default=None,
                        help="chunk_id within --base-jsonl to use as additional fixed variables")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--max-chunks", type=int, default=None,
                        help="optional smoke-test cap on newly processed chunks")
    parser.add_argument("--prune-prefix-ap", action="store_true",
                        help="for degree-vars, do not generate branches whose selected split values already contain a 3-AP")
    parser.add_argument("--quiet", action="store_true",
                        help="write JSONL normally but suppress per-chunk stdout")
    parser.add_argument("--progress-every", type=int, default=0,
                        help="when --quiet is set, print a compact progress row every N processed chunks")
    parser.add_argument("--window-bounds", type=Path, default=None,
                        help="OEIS A003002 b-file; adds window-cardinality constraints.")
    parser.add_argument("--pair-clauses-window", type=str, default=None,
                        help="LO,HI: forward targeted pair-AND Tseitin propagators to each CP-SAT solve.")
    parser.add_argument("--stop-on-feasible", action="store_true", default=True)
    parser.add_argument("--only-chunk-id", type=int, default=None,
                        help="process exactly one chunk with this ID and exit. "
                             "Intended for SLURM array jobs where each task is one chunk.")
    parser.add_argument("--chunk-id-start", type=int, default=None,
                        help="process chunks with chunk_id >= this value")
    parser.add_argument("--chunk-id-end", type=int, default=None,
                        help="exclusive upper bound for chunk IDs to process")
    args = parser.parse_args()
    if args.only_chunk_id is not None:
        if args.chunk_id_start is not None or args.chunk_id_end is not None:
            parser.error("--only-chunk-id cannot be combined with --chunk-id-start/--chunk-id-end")
        args.chunk_id_start = args.only_chunk_id
        args.chunk_id_end = args.only_chunk_id + 1
    if (args.chunk_id_start is None) != (args.chunk_id_end is None):
        parser.error("--chunk-id-start and --chunk-id-end must be provided together")
    if args.chunk_id_start is not None and args.chunk_id_end <= args.chunk_id_start:
        parser.error("--chunk-id-end must be greater than --chunk-id-start")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    seen = existing_chunk_ids(args.output)
    hint = load_int_set(args.hint) if args.hint else []
    window_bounds = load_window_bounds(args.window_bounds) if args.window_bounds else {}
    pair_clauses_window: tuple[int, int] | None = None
    if args.pair_clauses_window:
        parts = [p.strip() for p in args.pair_clauses_window.split(",") if p.strip()]
        if len(parts) != 2:
            parser.error("--pair-clauses-window must be LO,HI")
        pair_clauses_window = (int(parts[0]), int(parts[1]))
    global_fixed_in = load_int_set(args.fix_in) if args.fix_in else []
    global_fixed_out = load_int_set(args.fix_out) if args.fix_out else []
    if args.base_jsonl or args.base_chunk_id is not None:
        if not args.base_jsonl or args.base_chunk_id is None:
            parser.error("--base-jsonl and --base-chunk-id must be provided together")
        base_row = load_jsonl_chunk(args.base_jsonl, args.base_chunk_id)
        global_fixed_in = merge_fixed(global_fixed_in, [int(x) for x in base_row.get("fixed_in", [])])
        global_fixed_out = merge_fixed(global_fixed_out, [int(x) for x in base_row.get("fixed_out", [])])
    global_overlap = sorted(set(global_fixed_in) & set(global_fixed_out))
    if global_overlap:
        parser.error(f"--fix-in and --fix-out overlap: {global_overlap[:10]}")
    split_count = args.split_count if args.split_count is not None else args.pairs
    if args.strategy == "endpoint-pairs":
        assignments = prefix_assignments(args.N, split_count)
        split_variables: list[int] = []
    else:
        if args.split_vars:
            explicit_variables = load_int_set(args.split_vars)
            already_fixed = set(global_fixed_in) | set(global_fixed_out)
            split_variables = [value for value in explicit_variables if value not in already_fixed][:split_count]
        else:
            split_variables = degree_split_variables(args.N, split_count)
        assignments = variable_assignments(
            args.N,
            split_variables,
            prune_prefix_ap=args.prune_prefix_ap,
            prune_base_in=global_fixed_in,
        )

    started = time.time()
    processed = 0
    feasible_found = False
    with args.output.open("a", encoding="utf-8") as fh:
        for assignment in assignments:
            chunk_id = assignment["chunk_id"]
            if args.chunk_id_start is not None and chunk_id < args.chunk_id_start:
                continue
            if args.chunk_id_end is not None and chunk_id >= args.chunk_id_end:
                break
            if chunk_id in seen:
                continue
            if args.max_chunks is not None and processed >= args.max_chunks:
                break

            assignment_in = assignment["fixed_in"]
            assignment_out = assignment["fixed_out"]
            fixed_in = merge_fixed(global_fixed_in, assignment_in)
            fixed_out = merge_fixed(global_fixed_out, assignment_out)
            overlap = sorted(set(fixed_in) & set(fixed_out))
            if overlap:
                row = {
                    "chunk_id": chunk_id,
                    "N": args.N,
                    "K": args.K,
                    "strategy": args.strategy,
                    "split_count": split_count,
                    "split_variables": split_variables,
                    "prune_prefix_ap": args.prune_prefix_ap,
                    "branch_order": args.branch_order,
                    "branch_value": args.branch_value,
                    "fixed_search": args.fixed_search,
                    "global_fixed_in": global_fixed_in,
                    "global_fixed_out": global_fixed_out,
                    "assignment_fixed_in": assignment_in,
                    "assignment_fixed_out": assignment_out,
                    "fixed_in": fixed_in,
                    "fixed_out": fixed_out,
                    "prefix": assignment["prefix"],
                    "status": "SKIPPED_FIXED_CONFLICT",
                    "seconds": 0.0,
                    "branches": 0,
                    "conflicts": 0,
                    "certifies": True,
                }
                fh.write(json.dumps(row, sort_keys=True) + "\n")
                fh.flush()
                processed += 1
                if not args.quiet or (args.progress_every and processed % args.progress_every == 0):
                    print(json.dumps({
                        "chunk_id": row["chunk_id"],
                        "status": row["status"],
                        "seconds": row["seconds"],
                        "processed_this_run": processed,
                    }), flush=True)
                continue
            reason = skip_reason(args.N, args.K, fixed_in, fixed_out)
            row = {
                "chunk_id": chunk_id,
                "N": args.N,
                "K": args.K,
                "strategy": args.strategy,
                "split_count": split_count,
                "split_variables": split_variables,
                "prune_prefix_ap": args.prune_prefix_ap,
                "branch_order": args.branch_order,
                "branch_value": args.branch_value,
                "fixed_search": args.fixed_search,
                "global_fixed_in": global_fixed_in,
                "global_fixed_out": global_fixed_out,
                "assignment_fixed_in": assignment_in,
                "assignment_fixed_out": assignment_out,
                "fixed_in": fixed_in,
                "fixed_out": fixed_out,
                "prefix": assignment["prefix"],
            }

            if reason:
                row.update({
                    "status": reason,
                    "seconds": 0.0,
                    "branches": 0,
                    "conflicts": 0,
                    "certifies": True,
                })
            else:
                result = solve_r3_cpsat(
                    args.N,
                    decision_size=args.K,
                    time_limit=args.chunk_time_limit,
                    workers=args.workers_per_chunk,
                    fixed_in=fixed_in,
                    fixed_out=fixed_out,
                    hint=hint,
                    branch_order=args.branch_order,
                    branch_value=args.branch_value,
                    fixed_search=args.fixed_search,
                    symmetry_break=True,
                    window_bounds=window_bounds,
                    pair_clauses_window=pair_clauses_window,
                )
                solver_status = result["solver_status_name"]
                if result["is_feasible_for_decision_size"]:
                    status = "FEASIBLE"
                    feasible_found = True
                elif solver_status == "INFEASIBLE":
                    status = "INFEASIBLE"
                else:
                    status = "UNKNOWN"
                row.update({
                    "status": status,
                    "solver_status_name": solver_status,
                    "seconds": result["seconds"],
                    "branches": result["branches"],
                    "conflicts": result["conflicts"],
                    "certifies": result["certifies_optimal"],
                    "witness": result["witness"] if status == "FEASIBLE" else [],
                    "witness_verified": result["witness_verified"],
                })

            fh.write(json.dumps(row, sort_keys=True) + "\n")
            fh.flush()
            processed += 1
            if not args.quiet or (args.progress_every and processed % args.progress_every == 0):
                print(json.dumps({
                    "chunk_id": row["chunk_id"],
                    "status": row["status"],
                    "seconds": row["seconds"],
                    "processed_this_run": processed,
                }), flush=True)
            if feasible_found and args.stop_on_feasible:
                break
            if args.only_chunk_id is not None:
                break

    summary = summarize_jsonl(args.output)
    print(json.dumps({
        "output": str(args.output),
        "processed_this_run": processed,
        "elapsed_seconds": round(time.time() - started, 4),
        **summary,
    }, indent=2), flush=True)
    return 2 if feasible_found else 0


if __name__ == "__main__":
    raise SystemExit(main())
