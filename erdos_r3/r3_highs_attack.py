#!/usr/bin/env python3
"""HiGHS MIP attack on the 45 surviving r_3(212) UNKNOWN chunks.

For each UNKNOWN row in a recap300-style JSONL, build the equivalent
mixed-integer feasibility model in HiGHS (via highspy) and solve with a
per-chunk wall cap.  Writes one JSONL row per chunk with status, time, and
LP root bound.

The model:

    x_i in {0, 1} for i = 1..N
    sum x_i == K
    x[1] = 1, x[N] = 1                              # endpoint forcing
    x[v] = 1 for v in fixed_in                      # broad split assignment
    x[v] = 0 for v in fixed_out                     # broad split assignment
    x[a] + x[b] + x[c] <= 2  for every 3-AP triple  # 3-AP-free
    sum_{i in [a, a+L-1]} x[i] <= r_3(L)            # window-cardinality

HiGHS provides:
  * LP relaxation at root (informative even when MIP solves long).
  * Cutting planes (Gomory, clique) and dual reductions.
  * Open-source, single-pip-install.

Why this might close residuals that CP-SAT cannot: HiGHS's LP-based bound
tightening can prune branches early where CP-SAT's propagation needs to
brute-force a deep subtree.

Requires:  pip install highspy

Typical use:

    python3 r3_highs_attack.py \\
        --input results/N212_K44_window100k_recap300_sample100.jsonl \\
        --status UNKNOWN \\
        --window-bounds results/b003002.txt \\
        --witness-hint results/N212_K43_witness.json \\
        --time-limit 3600 \\
        --output results/N212_K44_highs_attack_results.jsonl

To restrict to a few cases first (sanity):

    python3 r3_highs_attack.py ... --limit 3 --time-limit 600
"""

from __future__ import annotations

import argparse
import json
import math
import sys
import time
from pathlib import Path


# ---------------------------------------------------------------------------
# Model construction
# ---------------------------------------------------------------------------


def arithmetic_progressions(N: int) -> list[tuple[int, int, int]]:
    triples: list[tuple[int, int, int]] = []
    for b in range(1, N + 1):
        max_d = min(b - 1, N - b)
        for d in range(1, max_d + 1):
            triples.append((b - d, b, b + d))
    return triples


def load_window_bounds(path: Path) -> dict[int, int]:
    bounds: dict[int, int] = {}
    with path.open("r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            try:
                a, b = line.split()
                bounds[int(a)] = int(b)
            except ValueError:
                continue
    return bounds


def load_witness(path: Path) -> list[int]:
    with path.open("r", encoding="utf-8") as fh:
        raw = json.load(fh)
    if isinstance(raw, dict):
        for k in ("A", "witness"):
            if k in raw:
                return [int(v) for v in raw[k]]
    if isinstance(raw, list):
        return [int(v) for v in raw]
    raise ValueError(f"could not parse witness from {path}")


def build_and_solve(
    *,
    N: int,
    K: int,
    fixed_in: list[int],
    fixed_out: list[int],
    window_bounds: dict[int, int],
    triples: list[tuple[int, int, int]],
    time_limit: float,
    hint: list[int] | None = None,
    threads: int = 8,
    presolve: bool = True,
    log: bool = False,
    mip_report_level: int | None = None,
    log_dev_level: int | None = None,
    mip_min_logging_interval: float | None = None,
) -> dict:
    """Build the model in HiGHS and solve.  Returns a status/timing dict."""
    try:
        import highspy
    except ImportError as e:
        raise SystemExit(
            "highspy not installed.  Run:\n"
            "  /work/pi_ergezerm_wit_edu/ergezerm_wit_edu-conda/envs/soft/bin/python "
            "-m pip install --user highspy\n"
            f"(import error: {e})"
        )

    # Defensive: highspy carries some process-global state between Highs()
    # instances; without this, repeated calls in one process can fail with
    # status "Not Set" and 0 nodes.  resetGlobalScheduler clears that state.
    try:
        highspy.Highs.resetGlobalScheduler()
    except Exception:
        pass
    h = highspy.Highs()
    if not log:
        h.silent()

    inf = highspy.kHighsInf
    n_vars = N

    # Variable bounds: x in [0, 1]; integrality set later.
    lb = [0.0] * n_vars
    ub = [1.0] * n_vars
    obj = [0.0] * n_vars  # feasibility problem; use sum-constraint instead.

    # Apply endpoint forcing and fixed_in/out by tightening bounds.
    pinned_in = set(fixed_in) | {1, N}
    pinned_out = set(fixed_out)
    if pinned_in & pinned_out:
        return {"status": "INVALID", "reason": "fixed_in ∩ fixed_out non-empty"}
    for v in pinned_in:
        lb[v - 1] = 1.0
        ub[v - 1] = 1.0
    for v in pinned_out:
        lb[v - 1] = 0.0
        ub[v - 1] = 0.0

    for i in range(n_vars):
        h.addVar(lb[i], ub[i])

    # Sum constraint: sum x_i == K
    h.addRow(K, K, n_vars, list(range(n_vars)), [1.0] * n_vars)

    # 3-AP constraints: x[a] + x[b] + x[c] <= 2
    for a, b, c in triples:
        h.addRow(-inf, 2.0, 3, [a - 1, b - 1, c - 1], [1.0, 1.0, 1.0])

    # Window-cardinality: sum_{[start, start+L-1]} x[i] <= r_3(L)
    win_added = 0
    for L in range(2, N + 1):
        rL = window_bounds.get(L)
        if rL is None or rL >= L:
            continue
        for start in range(0, N - L + 1):
            idx = list(range(start, start + L))
            h.addRow(-inf, float(rL), L, idx, [1.0] * L)
            win_added += 1

    # Integrality
    h.changeColsIntegrality(
        n_vars,
        list(range(n_vars)),
        [highspy.HighsVarType.kInteger] * n_vars,
    )

    # Solver options
    h.setOptionValue("time_limit", float(time_limit))
    h.setOptionValue("threads", int(threads))
    if log:
        h.setOptionValue("output_flag", True)
        h.setOptionValue("log_to_console", True)
    if mip_report_level is not None:
        h.setOptionValue("mip_report_level", int(mip_report_level))
    if log_dev_level is not None:
        h.setOptionValue("log_dev_level", int(log_dev_level))
    if mip_min_logging_interval is not None:
        h.setOptionValue("mip_min_logging_interval", float(mip_min_logging_interval))
    if presolve:
        h.setOptionValue("presolve", "on")
    else:
        h.setOptionValue("presolve", "off")
    # Encourage feasibility quickly if a feasible solution exists.
    h.setOptionValue("mip_heuristic_effort", 0.2)

    # Optional MIP start from hint (only the values consistent with bounds).
    if hint:
        # HiGHS API for hints is limited; we set integer values via passColSolution
        # AFTER first run.  For now, just rely on the LP relaxation + branching.
        pass

    t0 = time.time()
    h.run()
    wall = time.time() - t0

    info = h.getInfo()
    model_status = h.getModelStatus()
    status_name = h.modelStatusToString(model_status)
    sol = h.getSolution()
    objective = float(info.objective_function_value)
    lp_root = float(info.mip_dual_bound)
    mip_gap = float(info.mip_gap) if info.mip_node_count else None
    nodes = int(info.mip_node_count)

    # Map to our INF/UNK/FEAS schema.
    if "Infeasible" in status_name:
        status_label = "INFEASIBLE"
    elif "Optimal" in status_name:
        # For a feasibility decision problem, Optimal means we found a feasible
        # K-set assignment.
        status_label = "FEASIBLE"
    elif "Time" in status_name or "Iteration" in status_name:
        status_label = "UNKNOWN"
    else:
        status_label = f"OTHER:{status_name}"

    witness: list[int] = []
    if status_label == "FEASIBLE":
        for i, val in enumerate(sol.col_value):
            if val > 0.5:
                witness.append(i + 1)

    return {
        "status": status_label,
        "highs_status": status_name,
        "seconds": round(wall, 3),
        "lp_dual_bound": lp_root,
        "objective": objective,
        "mip_nodes": nodes,
        "mip_gap": mip_gap,
        "window_constraints_added": win_added,
        "ap_constraints": len(triples),
        "mip_report_level": mip_report_level,
        "log_dev_level": log_dev_level,
        "witness": witness,
    }


# ---------------------------------------------------------------------------
# Driver
# ---------------------------------------------------------------------------


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--input", type=Path, required=True,
                   help="JSONL file with UNKNOWN rows to re-attack with HiGHS.")
    p.add_argument("--status", default="UNKNOWN",
                   help="Filter input rows by this status (default UNKNOWN).")
    p.add_argument("--N", type=int, default=212)
    p.add_argument("--K", type=int, default=44)
    p.add_argument("--window-bounds", type=Path, required=True)
    p.add_argument("--witness-hint", type=Path, default=None)
    p.add_argument("--time-limit", type=float, default=3600.0,
                   help="Per-chunk wall cap in seconds (default 3600 = 1h).")
    p.add_argument("--threads", type=int, default=8)
    p.add_argument("--limit", type=int, default=None,
                   help="Process only the first N chunks (sanity).")
    p.add_argument("--only-chunk-id", type=int, default=None,
                   help="Process exactly one chunk_id and exit.  Use for SLURM array tasks.")
    p.add_argument("--array-index", type=int, default=None,
                   help="Process the row at this 0-based index in the filtered input list. "
                        "Use this when SLURM_ARRAY_TASK_ID indexes into the input rather than chunk_id.")
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--log", action="store_true",
                   help="Show HiGHS log output (default suppressed).")
    p.add_argument("--mip-report-level", type=int, default=None,
                   help="HiGHS mip_report_level option for more detailed MIP progress logs.")
    p.add_argument("--log-dev-level", type=int, default=None,
                   help="HiGHS log_dev_level option for developer-level logs.")
    p.add_argument("--mip-min-logging-interval", type=float, default=None,
                   help="HiGHS mip_min_logging_interval option in seconds.")
    args = p.parse_args()

    window_bounds = load_window_bounds(args.window_bounds)
    triples = arithmetic_progressions(args.N)
    hint = load_witness(args.witness_hint) if args.witness_hint else None

    # Load input rows.
    in_rows = []
    with args.input.open("r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            row = json.loads(line)
            if row.get("status") == args.status:
                in_rows.append(row)
    if args.only_chunk_id is not None:
        in_rows = [r for r in in_rows if int(r.get("chunk_id", -1)) == args.only_chunk_id]
        if not in_rows:
            print(f"chunk_id {args.only_chunk_id} not found among {args.status} rows.", file=sys.stderr)
            return 2
    if args.array_index is not None:
        if args.array_index < 0 or args.array_index >= len(in_rows):
            print(f"array-index {args.array_index} out of range [0, {len(in_rows)}).", file=sys.stderr)
            return 2
        in_rows = [in_rows[args.array_index]]
    if args.limit:
        in_rows = in_rows[: args.limit]

    print(f"Attacking {len(in_rows)} chunks with HiGHS "
          f"(time-limit={args.time_limit}s, threads={args.threads})",
          flush=True)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    # Resume support: skip chunk_ids already in the output.
    done_ids: set[int] = set()
    if args.output.exists():
        with args.output.open("r", encoding="utf-8") as fh:
            for line in fh:
                if not line.strip():
                    continue
                try:
                    done_ids.add(int(json.loads(line)["chunk_id"]))
                except (KeyError, ValueError):
                    continue
        print(f"Resuming: {len(done_ids)} chunks already done", flush=True)

    with args.output.open("a", encoding="utf-8") as out_fh:
        for row in in_rows:
            cid = int(row.get("chunk_id"))
            if cid in done_ids:
                continue
            fixed_in = [int(v) for v in row.get("fixed_in", [])]
            fixed_out = [int(v) for v in row.get("fixed_out", [])]
            t0 = time.time()
            try:
                result = build_and_solve(
                    N=args.N,
                    K=args.K,
                    fixed_in=fixed_in,
                    fixed_out=fixed_out,
                    window_bounds=window_bounds,
                    triples=triples,
                    time_limit=args.time_limit,
                    hint=hint,
                    threads=args.threads,
                    log=args.log,
                    mip_report_level=args.mip_report_level,
                    log_dev_level=args.log_dev_level,
                    mip_min_logging_interval=args.mip_min_logging_interval,
                )
            except Exception as e:
                result = {
                    "status": "ERROR",
                    "error": repr(e),
                    "seconds": round(time.time() - t0, 3),
                }
            row_out = {
                "chunk_id": cid,
                "fixed_in_count": len(fixed_in),
                "fixed_out_count": len(fixed_out),
                "input_status": row.get("status"),
                "input_seconds": row.get("seconds"),
                **result,
            }
            out_fh.write(json.dumps(row_out, sort_keys=True) + "\n")
            out_fh.flush()
            print(json.dumps({
                "chunk_id": cid,
                "status": result.get("status"),
                "seconds": result.get("seconds"),
                "mip_nodes": result.get("mip_nodes"),
                "lp_dual_bound": result.get("lp_dual_bound"),
            }), flush=True)
            # Stop the run immediately if a FEASIBLE 44-set appears.
            if result.get("status") == "FEASIBLE":
                print("STOP: FEASIBLE row found.  Verify witness with r3_verify.py before any further action.",
                      flush=True)
                break

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
