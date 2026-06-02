#!/usr/bin/env python3
"""Cost model for the r_3(212) = 43 upper-bound campaign.

Reads sample-100 and/or sample-500 depth-16 refinement JSONLs (or pre-computed
summary JSONs) and produces:

  * per-base-chunk solver-time and row-count distributions
  * calibrated CPU-hour estimate per UNKNOWN refinement
  * full-sweep cost projections across UNKNOWN-rate assumptions
  * CSV table and a small text report

Run locally after rsyncing the relevant Unity result files.  Typical use:

    python3 r3_cost_model.py \
        --refine-glob "results/refine_N212_K44_window100k_sample100_chunk*_next16_60.jsonl" \
        --refine-glob "results/refine_N212_K44_window100k_sample500_chunk*_next16_60.jsonl" \
        --broad-rows 100000 \
        --broad-unknowns 6071 \
        --full-sweep-chunks 12582912 \
        --workers-per-chunk 8 \
        --out-csv results/r3_cost_model.csv \
        --out-report results/r3_cost_model.txt
"""

from __future__ import annotations

import argparse
import glob
import json
import math
import os
import re
import statistics
import sys
from collections import defaultdict
from typing import Iterable

# ---------------------------------------------------------------------------
# Sample ingestion
# ---------------------------------------------------------------------------

BASE_RE = re.compile(r"chunk([0-9]+)_next[0-9]+_[0-9]+\.jsonl$")


def iter_jsonl(path: str) -> Iterable[dict]:
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                yield json.loads(line)
            except json.JSONDecodeError:
                continue


def summarize_refine_file(path: str) -> dict:
    """Return per-file aggregate stats for a depth-16 refinement JSONL."""
    rows = 0
    secs = 0.0
    status_counts = defaultdict(int)
    secs_min = math.inf
    secs_max = 0.0
    for row in iter_jsonl(path):
        rows += 1
        # r3_split_cpsat writes the per-subchunk wall time under "seconds".
        # Older runs occasionally use "solver_seconds"; fall back to that.
        if "seconds" in row:
            s = float(row.get("seconds", 0.0) or 0.0)
        else:
            s = float(row.get("solver_seconds", 0.0) or 0.0)
        secs += s
        if s < secs_min:
            secs_min = s
        if s > secs_max:
            secs_max = s
        status_counts[row.get("status", "UNKNOWN")] += 1
    base_match = BASE_RE.search(os.path.basename(path))
    base_id = int(base_match.group(1)) if base_match else None
    return {
        "path": path,
        "base_chunk_id": base_id,
        "rows": rows,
        "solver_seconds_sum": secs,
        "solver_seconds_min": (secs_min if rows else 0.0),
        "solver_seconds_max": secs_max,
        "status_counts": dict(status_counts),
    }


def collect_refine(paths: list[str]) -> list[dict]:
    seen: dict[int, dict] = {}
    for path in paths:
        if not os.path.isfile(path):
            continue
        s = summarize_refine_file(path)
        bid = s["base_chunk_id"]
        if bid is None:
            continue
        # If a base chunk is matched by multiple files (sample100 and
        # sample500 may overlap), prefer the one with more rows.
        prior = seen.get(bid)
        if prior is None or s["rows"] > prior["rows"]:
            seen[bid] = s
    return list(seen.values())


# ---------------------------------------------------------------------------
# Statistics
# ---------------------------------------------------------------------------


def percentiles(values: list[float], pcts: list[float]) -> dict[str, float]:
    if not values:
        return {f"p{int(p)}": 0.0 for p in pcts}
    s = sorted(values)
    out = {}
    n = len(s)
    for p in pcts:
        # linear interpolation
        if n == 1:
            out[f"p{int(p)}"] = s[0]
            continue
        k = (p / 100.0) * (n - 1)
        f = int(math.floor(k))
        c = int(math.ceil(k))
        if f == c:
            out[f"p{int(p)}"] = s[f]
        else:
            out[f"p{int(p)}"] = s[f] + (s[c] - s[f]) * (k - f)
    return out


def describe(name: str, vals: list[float]) -> dict[str, float]:
    if not vals:
        return {"name": name, "n": 0}
    p = percentiles(vals, [10, 25, 50, 75, 90, 95, 99])
    return {
        "name": name,
        "n": len(vals),
        "mean": statistics.fmean(vals),
        "stdev": statistics.pstdev(vals) if len(vals) > 1 else 0.0,
        "min": min(vals),
        "max": max(vals),
        **p,
    }


# ---------------------------------------------------------------------------
# Cost projection
# ---------------------------------------------------------------------------


def project_full_sweep(
    *,
    full_sweep_chunks: int,
    broad_seconds_per_chunk: float,
    workers_per_chunk: int,
    cost_per_unknown_cpu_seconds: float,
    unknown_rates: list[float],
    core_counts: list[int],
) -> list[dict]:
    """Project CPU-hours and wall-days under several UNK-rate assumptions.

    broad_seconds_per_chunk is the *wall* time per broad chunk on
    workers_per_chunk cores (so CPU-seconds = workers_per_chunk * wall).
    """
    broad_cpu_s = full_sweep_chunks * broad_seconds_per_chunk * workers_per_chunk

    rows = []
    for rate in unknown_rates:
        n_unknown = int(round(full_sweep_chunks * rate))
        refine_cpu_s = n_unknown * cost_per_unknown_cpu_seconds
        total_cpu_h = (broad_cpu_s + refine_cpu_s) / 3600.0
        row = {
            "unknown_rate": rate,
            "n_unknown": n_unknown,
            "broad_cpu_hours": broad_cpu_s / 3600.0,
            "refine_cpu_hours": refine_cpu_s / 3600.0,
            "total_cpu_hours": total_cpu_h,
        }
        for ncores in core_counts:
            row[f"wall_days_{ncores}cores"] = total_cpu_h / ncores / 24.0
        rows.append(row)
    return rows


# ---------------------------------------------------------------------------
# Reporting
# ---------------------------------------------------------------------------


def write_csv(path: str, header: list[str], rows: list[dict]) -> None:
    with open(path, "w") as f:
        f.write(",".join(header) + "\n")
        for r in rows:
            f.write(",".join(str(r.get(k, "")) for k in header) + "\n")


def fmt_pct(x: float) -> str:
    return f"{100.0 * x:.2f}%"


def fmt_hours(h: float) -> str:
    if h < 1.0:
        return f"{h * 60.0:.1f} min"
    if h < 48.0:
        return f"{h:.1f} h"
    return f"{h / 24.0:.1f} d"


def write_report(
    *,
    path: str,
    refine_summaries: list[dict],
    secs_desc: dict,
    rows_desc: dict,
    broad_rows: int,
    broad_unknowns: int,
    broad_unknown_rate: float,
    median_unknown_wall: float,
    median_unknown_cpu_s: float,
    workers_per_chunk: int,
    full_sweep_chunks: int,
    projection: list[dict],
    core_counts: list[int],
    broad_seconds_per_chunk: float,
) -> None:
    lines: list[str] = []
    lines.append("r_3(212) = 43 upper-bound campaign — cost model report")
    lines.append("=" * 64)
    lines.append("")
    lines.append(f"Refinement files ingested: {len(refine_summaries)}")
    lines.append("")
    lines.append("Per-base depth-16 refinement wall-seconds (8-worker):")
    for k in ("n", "mean", "min", "p10", "p25", "p50", "p75", "p90", "p95", "p99", "max"):
        lines.append(f"  {k:>4}: {secs_desc.get(k, 'n/a')}")
    lines.append("")
    lines.append("Per-base row counts:")
    for k in ("n", "mean", "min", "p10", "p25", "p50", "p75", "p90", "p95", "p99", "max"):
        lines.append(f"  {k:>4}: {rows_desc.get(k, 'n/a')}")
    lines.append("")
    lines.append("Broad-pass calibration:")
    lines.append(f"  broad rows         : {broad_rows}")
    lines.append(f"  broad UNKNOWN      : {broad_unknowns}")
    lines.append(f"  broad UNK rate     : {fmt_pct(broad_unknown_rate)}")
    lines.append(f"  broad sec/chunk    : {broad_seconds_per_chunk:.3f} (wall on {workers_per_chunk} cores)")
    lines.append("")
    lines.append("Refinement calibration:")
    lines.append(f"  median wall-seconds per UNK base chunk : {median_unknown_wall:.2f}")
    lines.append(f"  median CPU-seconds per UNK base chunk  : {median_unknown_cpu_s:.2f}")
    lines.append("")
    lines.append(
        f"Full-sweep projection ({full_sweep_chunks:,} broad chunks,"
        f" 8-worker, median refinement cost):"
    )
    lines.append("")
    header = "  rate       N_unknown   broad_cpu_h   refine_cpu_h   total_cpu_h    " + "   ".join(
        f"{n}c wall" for n in core_counts
    )
    lines.append(header)
    for r in projection:
        cell = []
        cell.append(f"  {fmt_pct(r['unknown_rate']):>7}")
        cell.append(f"{r['n_unknown']:>12,}")
        cell.append(f"{r['broad_cpu_hours']:>13,.0f}")
        cell.append(f"{r['refine_cpu_hours']:>13,.0f}")
        cell.append(f"{r['total_cpu_hours']:>13,.0f}")
        for n in core_counts:
            cell.append(f"{fmt_hours(r[f'wall_days_{n}cores'] * 24.0):>9}")
        lines.append("  ".join(cell))
    lines.append("")
    with open(path, "w") as f:
        f.write("\n".join(lines) + "\n")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument(
        "--refine-glob",
        action="append",
        required=True,
        help="Glob (may be passed multiple times) of depth-16 refinement JSONLs.",
    )
    p.add_argument(
        "--broad-rows",
        type=int,
        default=100000,
        help="Number of broad chunks observed in the calibrating window batch.",
    )
    p.add_argument(
        "--broad-unknowns",
        type=int,
        default=6071,
        help="Number of UNKNOWN broad chunks observed.",
    )
    p.add_argument(
        "--broad-seconds-per-chunk",
        type=float,
        default=5.2,
        help="Average wall-seconds per broad chunk (8-worker).",
    )
    p.add_argument(
        "--full-sweep-chunks",
        type=int,
        default=12_582_912,
        help="Total broad chunks in the full depth-24 AP-pruned sweep.",
    )
    p.add_argument(
        "--workers-per-chunk",
        type=int,
        default=8,
        help="OR-Tools workers per chunk (multiplies wall→CPU seconds).",
    )
    p.add_argument(
        "--unknown-rates",
        type=str,
        default="0.06,0.10,0.15,0.20",
        help="Comma-separated UNK rate assumptions to project.",
    )
    p.add_argument(
        "--core-counts",
        type=str,
        default="500,1000,2000",
        help="Comma-separated Unity core counts to project wall days against.",
    )
    p.add_argument("--out-csv", type=str, default=None)
    p.add_argument("--out-report", type=str, default=None)
    p.add_argument("--out-per-base-csv", type=str, default=None)
    args = p.parse_args()

    paths: list[str] = []
    for pattern in args.refine_glob:
        paths.extend(sorted(glob.glob(pattern)))
    if not paths:
        print("No files matched any --refine-glob pattern.", file=sys.stderr)
        return 2

    summaries = collect_refine(paths)
    if not summaries:
        print("No parseable refinement summaries found.", file=sys.stderr)
        return 2

    secs = [s["solver_seconds_sum"] for s in summaries]
    rows = [s["rows"] for s in summaries]
    secs_desc = describe("wall_seconds", secs)
    rows_desc = describe("rows", rows)

    median_unknown_wall = secs_desc.get("p50", 0.0) or 0.0
    median_unknown_cpu_s = median_unknown_wall * args.workers_per_chunk

    broad_unknown_rate = (
        args.broad_unknowns / args.broad_rows if args.broad_rows else 0.0
    )

    unknown_rates = [float(x) for x in args.unknown_rates.split(",") if x.strip()]
    core_counts = [int(x) for x in args.core_counts.split(",") if x.strip()]

    projection = project_full_sweep(
        full_sweep_chunks=args.full_sweep_chunks,
        broad_seconds_per_chunk=args.broad_seconds_per_chunk,
        workers_per_chunk=args.workers_per_chunk,
        cost_per_unknown_cpu_seconds=median_unknown_cpu_s,
        unknown_rates=unknown_rates,
        core_counts=core_counts,
    )

    print(json.dumps({
        "n_refine_files": len(summaries),
        "wall_seconds_desc": secs_desc,
        "rows_desc": rows_desc,
        "broad_unknown_rate": broad_unknown_rate,
        "median_unknown_cpu_seconds": median_unknown_cpu_s,
        "projection": projection,
    }, indent=2))

    if args.out_csv:
        header = (
            ["unknown_rate", "n_unknown", "broad_cpu_hours", "refine_cpu_hours", "total_cpu_hours"]
            + [f"wall_days_{n}cores" for n in core_counts]
        )
        write_csv(args.out_csv, header, projection)

    if args.out_per_base_csv:
        header = ["base_chunk_id", "rows", "solver_seconds_sum", "INFEASIBLE", "UNKNOWN", "FEASIBLE"]
        per_base_rows = []
        for s in summaries:
            sc = s["status_counts"]
            per_base_rows.append({
                "base_chunk_id": s["base_chunk_id"],
                "rows": s["rows"],
                "solver_seconds_sum": s["solver_seconds_sum"],
                "INFEASIBLE": sc.get("INFEASIBLE", 0),
                "UNKNOWN": sc.get("UNKNOWN", 0),
                "FEASIBLE": sc.get("FEASIBLE", 0),
            })
        write_csv(args.out_per_base_csv, header, per_base_rows)

    if args.out_report:
        write_report(
            path=args.out_report,
            refine_summaries=summaries,
            secs_desc=secs_desc,
            rows_desc=rows_desc,
            broad_rows=args.broad_rows,
            broad_unknowns=args.broad_unknowns,
            broad_unknown_rate=broad_unknown_rate,
            median_unknown_wall=median_unknown_wall,
            median_unknown_cpu_s=median_unknown_cpu_s,
            workers_per_chunk=args.workers_per_chunk,
            full_sweep_chunks=args.full_sweep_chunks,
            projection=projection,
            core_counts=core_counts,
            broad_seconds_per_chunk=args.broad_seconds_per_chunk,
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
