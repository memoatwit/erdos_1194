"""
Adaptive proof manager for the r_3(N) upper-bound CP-SAT sweep.

Given a broad split JSONL (e.g. depth-24 over witness variables), this:

  1. parses the JSONL and reports per-status counts plus the list of UNKNOWN
     base chunk IDs;
  2. inspects each pre-existing refinement file and reports whether the
     UNKNOWN base chunk is closed, partial, or untouched;
  3. emits a queue of refinement commands ready to paste into a shell;
  4. optionally executes the queue via subprocess if `--exec` is given;
  5. supports two-level refinement: when a refinement file contains its
     own UNKNOWN sub-chunks, schedules a deeper refinement for them;
  6. stops the queue immediately if any prior file reports FEASIBLE (the
     win condition for a counterexample to r_3(212) = 43).

It does not run CP-SAT itself; all heavy lifting goes through the existing
`r3_split_cpsat.py` runner.  The point is to encode the user's manual
"close-the-unknowns" loop as a stateless replayable script.

Usage:

  python3 r3_proof_manager.py --plan \
      --broad results/N212_K44_split_witness24_endpoints_pruned_600.jsonl \
      --N 212 --K 44 \
      --split-vars results/N212_K43_witness_degree_order.json \
      --fix-in results/N212_K44_force_endpoints.json \
      --hint results/N212_K43_witness.json \
      --refine-depths 16,8 \
      --chunk-time-limit 60 \
      --workers-per-chunk 8 \
      --refine-out-template "results/refine_N212_K44_witness24_chunk{base}_next{depth}_60.jsonl"

Add `--exec /Users/memo/miniconda3/bin/python3` to actually run the queue.
"""
from __future__ import annotations

import argparse
import json
import os
import shlex
import subprocess
import sys
from collections import Counter
from pathlib import Path
from typing import Iterable


HERE = Path(__file__).resolve().parent


def parse_jsonl(path: Path) -> list[dict]:
    rows: list[dict] = []
    if not path.exists():
        return rows
    with path.open("r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return rows


def summarize_rows(rows: Iterable[dict]) -> Counter:
    return Counter(r.get("status", "UNKNOWN") for r in rows)


def feasible_in(rows: Iterable[dict]) -> dict | None:
    for r in rows:
        if r.get("status") == "FEASIBLE":
            return r
    return None


def unknown_chunk_ids(rows: Iterable[dict]) -> list[int]:
    return sorted(r["chunk_id"] for r in rows if r.get("status") == "UNKNOWN")


def refine_command(
    *,
    py: str,
    runner: Path,
    N: int,
    K: int,
    depth: int,
    split_count: int,
    split_vars_path: Path,
    base_jsonl: Path,
    base_chunk_id: int,
    chunk_time_limit: int,
    workers_per_chunk: int,
    hint: Path | None,
    fix_in: Path | None,
    output: Path,
    extra: list[str] | None = None,
) -> list[str]:
    cmd = [
        py, str(runner),
        "--N", str(N),
        "--K", str(K),
        "--pairs", str(depth),
        "--strategy", "degree-vars",
        "--split-count", str(split_count),
        "--split-vars", str(split_vars_path),
        "--base-jsonl", str(base_jsonl),
        "--base-chunk-id", str(base_chunk_id),
        "--chunk-time-limit", str(chunk_time_limit),
        "--workers-per-chunk", str(workers_per_chunk),
        "--prune-prefix-ap",
        "--branch-order", "degree",
        "--branch-value", "min",
        "--fixed-search",
        "--quiet",
        "--progress-every", "5000",
        "--output", str(output),
    ]
    if hint is not None:
        cmd.extend(["--hint", str(hint)])
    if fix_in is not None:
        cmd.extend(["--fix-in", str(fix_in)])
    if extra:
        cmd.extend(extra)
    return cmd


def plan_refinements(
    *,
    broad_path: Path,
    N: int,
    K: int,
    split_vars_path: Path,
    fix_in: Path | None,
    hint: Path | None,
    refine_depths: list[int],
    chunk_time_limit: int,
    workers_per_chunk: int,
    refine_out_template: str,
    py: str,
    runner: Path,
    skip_closed: set[int] | None = None,
) -> list[dict]:
    """Produce an ordered list of {description, command, output_path, base, depth} dicts.

    Depth scheme: refine_depths[0] is the first refinement on top of broad,
    refine_depths[1] is the refinement on UNKNOWN sub-chunks of the first
    refinement, etc.  The base_jsonl is updated at each level.
    """
    plan: list[dict] = []
    broad_rows = parse_jsonl(broad_path)
    if not broad_rows:
        raise RuntimeError(f"No rows in {broad_path}")

    feas = feasible_in(broad_rows)
    if feas:
        return [{"description": "PROOF FALSIFIED: FEASIBLE row in broad JSONL",
                 "command": None, "feasible_row": feas}]

    unk = unknown_chunk_ids(broad_rows)
    if not unk:
        return [{"description": "Broad JSONL has no UNKNOWN rows.  Nothing to refine.",
                 "command": None}]

    # Closure heuristic: a depth-16 refinement of a depth-24 base chunk should
    # have on the order of CLOSED_THRESHOLD rows when all sub-chunks have been
    # enumerated.  We treat row counts >= CLOSED_THRESHOLD AND zero UNKNOWN as
    # closed; everything else is partial / not started and gets a resume.  The
    # runner is idempotent (skips done chunk_ids), so emitting a resume on an
    # already-closed file is harmless.
    CLOSED_THRESHOLD = 20000  # observed: 27648 for closed depth-16 refinements

    skip_closed = skip_closed or set()

    for base_chunk_id in unk:
        if base_chunk_id in skip_closed:
            plan.append({
                "description": f"chunk {base_chunk_id} marked closed by --skip-closed",
                "command": None,
                "base_chunk_id": base_chunk_id,
            })
            continue
        # Look at first refinement
        depth1 = refine_depths[0]
        out1 = Path(refine_out_template.format(base=base_chunk_id, depth=depth1))
        out1 = (HERE / out1) if not out1.is_absolute() else out1
        rows1 = parse_jsonl(out1)
        if rows1:
            feas1 = feasible_in(rows1)
            if feas1:
                plan.append({"description": f"PROOF FALSIFIED at refine-1 of chunk {base_chunk_id}",
                             "command": None, "feasible_row": feas1})
                return plan
        status1 = summarize_rows(rows1)
        unk1 = unknown_chunk_ids(rows1) if rows1 else []
        n_rows1 = len(rows1) if rows1 else 0
        is_closed = (n_rows1 >= CLOSED_THRESHOLD) and (not unk1)
        if is_closed:
            plan.append({
                "description": f"chunk {base_chunk_id} closed ({n_rows1} sub-chunks, all INFEASIBLE)",
                "command": None,
                "output": str(out1),
                "base_chunk_id": base_chunk_id,
                "current_status": dict(status1),
            })
            continue
        # Either no refinement file yet, partial, or has UNKNOWNs — emit resume/start.
        if n_rows1 == 0:
            label = "START"
        elif unk1:
            label = f"RESUME ({n_rows1} done, {len(unk1)} UNKNOWN)"
        else:
            label = f"RESUME PARTIAL ({n_rows1} done, expected >= {CLOSED_THRESHOLD})"
        cmd = refine_command(
            py=py, runner=HERE / "r3_split_cpsat.py", N=N, K=K,
            depth=depth1, split_count=depth1,
            split_vars_path=split_vars_path,
            base_jsonl=broad_path, base_chunk_id=base_chunk_id,
            chunk_time_limit=chunk_time_limit,
            workers_per_chunk=workers_per_chunk,
            hint=hint, fix_in=fix_in,
            output=out1,
        )
        plan.append({
            "description": f"refine-1 chunk {base_chunk_id} (depth {depth1}) {label}",
            "command": cmd,
            "output": str(out1),
            "base_chunk_id": base_chunk_id,
            "depth": depth1,
            "level": 1,
            "current_status": dict(status1),
        })
        # Plan refine-2 for each lingering UNKNOWN sub-chunk if a second depth is given.
        if unk1 and len(refine_depths) >= 2:
            depth2 = refine_depths[1]
            for sub_unknown_id in unk1:
                out2 = Path(str(out1).replace(
                    f"_chunk{base_chunk_id}_next{depth1}_",
                    f"_chunk{base_chunk_id}_{sub_unknown_id}_next{depth2}_",
                ))
                cmd2 = refine_command(
                    py=py, runner=HERE / "r3_split_cpsat.py", N=N, K=K,
                    depth=depth2, split_count=depth2,
                    split_vars_path=split_vars_path,
                    base_jsonl=out1, base_chunk_id=sub_unknown_id,
                    chunk_time_limit=chunk_time_limit,
                    workers_per_chunk=workers_per_chunk,
                    hint=hint, fix_in=fix_in,
                    output=out2,
                )
                plan.append({
                    "description": f"refine-2 chunk {base_chunk_id}/{sub_unknown_id} (depth {depth2})",
                    "command": cmd2,
                    "output": str(out2),
                    "base_chunk_id": base_chunk_id,
                    "sub_chunk_id": sub_unknown_id,
                    "depth": depth2,
                    "level": 2,
                })

    return plan


def print_plan(plan: list[dict], *, show_commands: bool) -> None:
    print(f"\n=== Adaptive proof plan: {len(plan)} entries ===\n")
    open_count = 0
    for i, item in enumerate(plan):
        marker = " " if item.get("command") is None else "*"
        if item.get("command") is not None:
            open_count += 1
        print(f"[{i:>3}] {marker} {item['description']}")
        if "current_status" in item:
            print(f"        current: {item['current_status']}")
        if show_commands and item.get("command"):
            print(f"        $ {' '.join(shlex.quote(s) for s in item['command'])}")
    print(f"\nTotal queued runs: {open_count}")


def run_plan(plan: list[dict]) -> int:
    failed = 0
    for i, item in enumerate(plan):
        if item.get("command") is None:
            continue
        print(f"\n[{i}] RUN: {item['description']}", flush=True)
        print(f"     output: {item.get('output')}", flush=True)
        try:
            res = subprocess.run(item["command"], check=False)
        except KeyboardInterrupt:
            print("Interrupted.", file=sys.stderr)
            return 130
        if res.returncode != 0:
            failed += 1
            print(f"   returncode = {res.returncode}")
        # Check for FEASIBLE
        if item.get("output"):
            rows = parse_jsonl(Path(item["output"]))
            feas = feasible_in(rows)
            if feas:
                print(f"\n!!! FEASIBLE row found at {item['output']} — proof of r_3(212) = 43 is FALSIFIED.")
                print(json.dumps(feas, indent=2, default=str))
                return 0
    print(f"\nFinished plan ({failed} commands failed).")
    return 0


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--broad", type=Path, required=True,
                   help="Broad split JSONL file (e.g. depth-24 over witness vars)")
    p.add_argument("--N", type=int, required=True)
    p.add_argument("--K", type=int, required=True)
    p.add_argument("--split-vars", type=Path, required=True)
    p.add_argument("--fix-in", type=Path, default=None)
    p.add_argument("--hint", type=Path, default=None)
    p.add_argument("--refine-depths", type=str, default="16",
                   help="Comma-sep list of refinement depths, e.g. 16,8 for two levels")
    p.add_argument("--chunk-time-limit", type=int, default=60)
    p.add_argument("--workers-per-chunk", type=int, default=8)
    p.add_argument("--refine-out-template", type=str, required=True,
                   help="Format string with {base} and {depth}, e.g. "
                        "results/refine_N212_K44_witness24_chunk{base}_next{depth}_60.jsonl")
    p.add_argument("--plan", action="store_true",
                   help="Print the queued plan only")
    p.add_argument("--exec", type=str, default=None,
                   help="Python interpreter path (e.g. /Users/memo/miniconda3/bin/python3) "
                        "to actually run the queue")
    p.add_argument("--show-commands", action="store_true")
    p.add_argument("--skip-closed", type=str, default="",
                   help="Comma-sep list of base chunk IDs already known to be closed by external refinements (e.g. depth-8 files). Example: --skip-closed 31")
    args = p.parse_args()

    depths = [int(d) for d in args.refine_depths.split(",") if d.strip()]
    if not depths:
        print("--refine-depths must be a non-empty comma-sep list", file=sys.stderr)
        return 2

    py = args.exec or "/usr/bin/env python3"

    skip_closed = set()
    if args.skip_closed:
        skip_closed = {int(x) for x in args.skip_closed.split(",") if x.strip()}

    plan = plan_refinements(
        broad_path=args.broad,
        N=args.N,
        K=args.K,
        split_vars_path=args.split_vars,
        fix_in=args.fix_in,
        hint=args.hint,
        refine_depths=depths,
        chunk_time_limit=args.chunk_time_limit,
        workers_per_chunk=args.workers_per_chunk,
        refine_out_template=args.refine_out_template,
        py=py,
        runner=HERE / "r3_split_cpsat.py",
        skip_closed=skip_closed,
    )

    print_plan(plan, show_commands=args.show_commands or not args.exec)

    if args.exec:
        return run_plan(plan)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
