"""
Run a resumable first-element split exact search for Erdős #156.

This wraps search156_v4, running one canonical first element per chunk and
writing a JSON checkpoint after each completed chunk.

Example:
  python3 erdos_156/run_split_exact.py --N 125 --k 7 --workers 8
"""
from __future__ import annotations

import argparse
import concurrent.futures
import json
import os
import subprocess
import time
from pathlib import Path
from typing import Any


THIS_DIR = Path(__file__).resolve().parent
DEFAULT_BINARY = THIS_DIR / "search156_v4"
DEFAULT_OUTPUT = THIS_DIR / "results" / "exact_156_N125_k7_split.json"


def load_checkpoint(path: Path, N: int, k: int, first_lo: int, first_hi: int) -> dict[str, Any]:
    if path.exists():
        with path.open("r", encoding="utf-8") as fh:
            return json.load(fh)
    return {
        "N": N,
        "k": k,
        "first_lo": first_lo,
        "first_hi": first_hi,
        "canonical_by_reflection": True,
        "status": "running",
        "started_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "chunks": [],
    }


def save_checkpoint(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with tmp.open("w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2)
        fh.write("\n")
    os.replace(tmp, path)


def run_one(binary: Path, N: int, k: int, first: int, time_limit: float, lex: bool) -> dict[str, Any]:
    cmd = [str(binary), str(N), str(k), str(time_limit), str(first), str(first)]
    if lex:
        cmd.append("lex")
    t0 = time.time()
    proc = subprocess.run(cmd, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    elapsed = time.time() - t0
    try:
        row = json.loads(proc.stdout)
    except json.JSONDecodeError:
        row = {
            "N": N,
            "k": k,
            "first_lo": first,
            "first_hi": first,
            "status": "parse_error",
            "stdout": proc.stdout,
            "stderr": proc.stderr,
        }
    row["returncode"] = proc.returncode
    row["wall_time_s"] = elapsed
    if proc.stderr.strip():
        row["stderr"] = proc.stderr.strip()
    return row


def summarize(data: dict[str, Any]) -> dict[str, Any]:
    chunks = data["chunks"]
    statuses = {}
    for row in chunks:
        statuses[row["status"]] = statuses.get(row["status"], 0) + 1
    complete = [
        row for row in chunks
        if row["status"] in {"infeasible", "feasible", "timeout"}
    ]
    total_time = sum(row.get("time_s", row.get("wall_time_s", 0.0)) for row in complete)
    total_nodes = sum(row.get("nodes", 0) for row in complete)
    data["summary"] = {
        "completed_chunks": len(complete),
        "status_counts": statuses,
        "total_reported_time_s": total_time,
        "total_nodes": total_nodes,
    }
    if any(row["status"] == "feasible" for row in chunks):
        data["status"] = "feasible"
        data["A"] = next(row["A"] for row in chunks if row["status"] == "feasible")
    elif len(complete) == data["first_hi"] - data["first_lo"] + 1 and all(
        row["status"] == "infeasible" for row in complete
    ):
        data["status"] = "infeasible"
        data["A"] = None
    elif any(row["status"] == "timeout" for row in chunks):
        data["status"] = "partial_timeout"
        data["A"] = None
    else:
        data["status"] = "running"
        data["A"] = None
    return data


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--N", type=int, required=True)
    parser.add_argument("--k", type=int, required=True)
    parser.add_argument("--first-lo", type=int, default=1)
    parser.add_argument("--first-hi", type=int, default=None)
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--time-limit", type=float, default=0.0,
                        help="per-first-element search limit; 0 means no limit")
    parser.add_argument("--binary", type=Path, default=DEFAULT_BINARY)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--lex", action="store_true")
    args = parser.parse_args()

    first_hi = args.first_hi if args.first_hi is not None else (args.N + 1) // 2
    data = load_checkpoint(args.output, args.N, args.k, args.first_lo, first_hi)
    done = {row["first_lo"] for row in data["chunks"] if row.get("status") in {"infeasible", "feasible"}}
    pending = [first for first in range(args.first_lo, first_hi + 1) if first not in done]

    print(f"Running N={args.N}, k={args.k}, first={args.first_lo}..{first_hi}, "
          f"workers={args.workers}, pending={len(pending)}", flush=True)
    save_checkpoint(args.output, summarize(data))

    with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as pool:
        future_to_first = {
            pool.submit(run_one, args.binary, args.N, args.k, first, args.time_limit, args.lex): first
            for first in pending
        }
        for future in concurrent.futures.as_completed(future_to_first):
            first = future_to_first[future]
            row = future.result()
            data["chunks"] = [old for old in data["chunks"] if old.get("first_lo") != first]
            data["chunks"].append(row)
            data["chunks"].sort(key=lambda item: item["first_lo"])
            data["updated_at"] = time.strftime("%Y-%m-%d %H:%M:%S")
            save_checkpoint(args.output, summarize(data))
            print(
                f"first={first:2d} status={row['status']} "
                f"time={row.get('time_s', row.get('wall_time_s', 0.0)):.3f}s "
                f"nodes={row.get('nodes', 0)}",
                flush=True,
            )
            if row["status"] == "feasible":
                print(f"Found witness: {row['A']}", flush=True)
                return 0

    data["finished_at"] = time.strftime("%Y-%m-%d %H:%M:%S")
    save_checkpoint(args.output, summarize(data))
    print(f"Final status: {data['status']}", flush=True)
    return 0 if data["status"] in {"infeasible", "feasible"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
