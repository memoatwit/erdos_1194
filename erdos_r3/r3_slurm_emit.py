"""
Emit Unity SLURM SBATCH scripts for the r_3(212) = 43 upper-bound campaign.

Two modes:

  --phase 1 : refinement queue from r3_proof_manager.  One SLURM task per
              UNKNOWN base chunk in the broad-24 JSONL (closes the prefix).

  --phase 2 : broad-24 sweep.  SLURM array job, one task per contiguous
              chunk-id range, depth 24.  Each task writes a shard JSONL file,
              then a separate r3_collect.py call merges them.

The emitted scripts assume Unity SLURM defaults:

  * `module load conda/latest` then `conda activate r3` (override via --env-init).
  * Per-task wall time = chunk-time-limit + 60s overhead.
  * 8 CPUs per task by default (overridable).
  * Output files under WORKDIR/results/.

Adapt the scheduler directives at the top of the emitted .sbatch file if
your Unity partition / account / time limit differ.

Usage:
  python3 r3_slurm_emit.py --phase 1 \
      --broad results/N212_K44_split_witness24_endpoints_pruned_600.jsonl \
      --skip-closed 31,63,95,126,127,159 \
      --out submit_phase1.sbatch

  python3 r3_slurm_emit.py --phase 2 \
      --chunk-start 575 --chunk-end 1574 \
      --chunks-per-task 100 \
      --out submit_phase2_575_1574.sbatch
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from collections import Counter


HERE = Path(__file__).resolve().parent
RESULTS = HERE / "results"


PHASE1_HEADER = """#!/bin/bash
#SBATCH --job-name=r3_212_phase1
#SBATCH --partition={partition}
#SBATCH --account={account}
#SBATCH --time={time}
#SBATCH --array=0-{nm1}{array_throttle}
#SBATCH --cpus-per-task={cpus}
#SBATCH --mem={mem}
#SBATCH --output={logdir}/phase1-%A_%a.out
#SBATCH --error={logdir}/phase1-%A_%a.err

set -euo pipefail
{env_init}

cd {workdir}

# Map SLURM_ARRAY_TASK_ID -> base chunk id via the embedded table.
TASKS=({task_list})
BASE_CHUNK_ID=${{TASKS[$SLURM_ARRAY_TASK_ID]}}

OUT="{workdir}/results/{refine_prefix}_chunk${{BASE_CHUNK_ID}}_next16_60.jsonl"

python3 "{workdir}/r3_split_cpsat.py" \\
  --N 212 --K 44 \\
  --pairs 16 \\
  --strategy degree-vars \\
  --split-count 16 \\
  --split-vars "{workdir}/results/{split_vars_name}" \\
  --base-jsonl "{broad}" \\
  --base-chunk-id "$BASE_CHUNK_ID" \\
  --chunk-time-limit {chunk_time_limit} \\
  --workers-per-chunk {workers_per_chunk} \\
  --hint "{workdir}/results/{hint_name}" \\
  --fix-in "{workdir}/results/N212_K44_force_endpoints.json" \\
  --window-bounds "{workdir}/results/b003002.txt" \\
  --prune-prefix-ap \\
  --branch-order degree \\
  --branch-value min \\
  --fixed-search \\
  --quiet \\
  --progress-every 5000 \\
  --output "$OUT"
"""


PHASE2_HEADER = """#!/bin/bash
#SBATCH --job-name=r3_212_p2_{start}_{end}
#SBATCH --partition={partition}
#SBATCH --account={account}
#SBATCH --time={time}
#SBATCH --array=0-{task_end}{array_throttle}
#SBATCH --cpus-per-task={cpus}
#SBATCH --mem={mem}
#SBATCH --output={logdir}/phase2-%A_%a.out
#SBATCH --error={logdir}/phase2-%A_%a.err

set -euo pipefail
{env_init}

cd {workdir}

CHUNK_START={start}
CHUNK_END={exclusive_end}
CHUNKS_PER_TASK={chunks_per_task}
RANGE_START=$((CHUNK_START + SLURM_ARRAY_TASK_ID * CHUNKS_PER_TASK))
RANGE_END=$((RANGE_START + CHUNKS_PER_TASK))
if [ "$RANGE_END" -gt "$CHUNK_END" ]; then
  RANGE_END="$CHUNK_END"
fi
RANGE_END_INCLUSIVE=$((RANGE_END - 1))

SHARD_DIR="{workdir}/{shard_dir}"
mkdir -p "$SHARD_DIR"
SHARD_FILE="$SHARD_DIR/chunks_$(printf '%08d' $RANGE_START)_$(printf '%08d' $RANGE_END_INCLUSIVE).jsonl"
TMP_SHARD_FILE="$SHARD_FILE.tmp_${{SLURM_JOB_ID}}_${{SLURM_ARRAY_TASK_ID}}"

# Skip if the final shard already exists and is non-empty (allows resume).
if [ -s "$SHARD_FILE" ]; then
  echo "[skip] $SHARD_FILE already exists"
  exit 0
fi
rm -f "$TMP_SHARD_FILE"

python3 "{workdir}/r3_split_cpsat.py" \\
  --N 212 --K 44 \\
  --pairs 24 \\
  --strategy degree-vars \\
  --split-count 24 \\
  --split-vars "{workdir}/results/{split_vars_name}" \\
  --chunk-id-start "$RANGE_START" \\
  --chunk-id-end "$RANGE_END" \\
  --chunk-time-limit {chunk_time_limit} \\
  --workers-per-chunk {workers_per_chunk} \\
  --hint "{workdir}/results/{hint_name}" \\
  --fix-in "{workdir}/results/N212_K44_force_endpoints.json" \\
  --window-bounds "{workdir}/results/b003002.txt" \\
  --prune-prefix-ap \\
  --branch-order degree \\
  --branch-value min \\
  --fixed-search \\
  --quiet \\
  --progress-every 5000 \\
  --output "$TMP_SHARD_FILE"

mv "$TMP_SHARD_FILE" "$SHARD_FILE"
"""


PHASE2_CHUNK_LIST_HEADER = """#!/bin/bash
#SBATCH --job-name=r3_212_p2_list
#SBATCH --partition={partition}
#SBATCH --account={account}
#SBATCH --time={time}
#SBATCH --array=0-{task_end}{array_throttle}
#SBATCH --cpus-per-task={cpus}
#SBATCH --mem={mem}
#SBATCH --output={logdir}/phase2-list-%A_%a.out
#SBATCH --error={logdir}/phase2-list-%A_%a.err

set -euo pipefail
{env_init}

cd {workdir}

CHUNK_IDS=({chunk_ids})
CHUNK_ID="${{CHUNK_IDS[$SLURM_ARRAY_TASK_ID]}}"

SHARD_DIR="{workdir}/{shard_dir}"
mkdir -p "$SHARD_DIR"
SHARD_FILE="$SHARD_DIR/chunk_$(printf '%08d' $CHUNK_ID).jsonl"
TMP_SHARD_FILE="$SHARD_FILE.tmp_${{SLURM_JOB_ID}}_${{SLURM_ARRAY_TASK_ID}}"

# Skip if the final shard already exists and is non-empty (allows resume).
if [ -s "$SHARD_FILE" ]; then
  echo "[skip] $SHARD_FILE already exists"
  exit 0
fi
rm -f "$TMP_SHARD_FILE"

python3 "{workdir}/r3_split_cpsat.py" \\
  --N 212 --K 44 \\
  --pairs 24 \\
  --strategy degree-vars \\
  --split-count 24 \\
  --split-vars "{workdir}/results/{split_vars_name}" \\
  --only-chunk-id "$CHUNK_ID" \\
  --chunk-time-limit {chunk_time_limit} \\
  --workers-per-chunk {workers_per_chunk} \\
  --hint "{workdir}/results/{hint_name}" \\
  --fix-in "{workdir}/results/N212_K44_force_endpoints.json" \\
  --window-bounds "{workdir}/results/b003002.txt" \\
  --prune-prefix-ap \\
  --branch-order degree \\
  --branch-value min \\
  --fixed-search \\
  --quiet \\
  --progress-every 5000 \\
  --output "$TMP_SHARD_FILE"

mv "$TMP_SHARD_FILE" "$SHARD_FILE"
"""


DEFAULTS = {
    "partition": "cpu",
    "account": "pi_ergezerm_wit_edu",
    "time": "02:00:00",
    "cpus": "8",
    "mem": "8G",
    # Direct PATH export to the known-good Unity prefix.  The user's .condarc
    # has duplicate envs_dirs so `conda activate r3` is brittle; use the
    # absolute prefix instead.
    "env_init": "export PATH=/work/pi_ergezerm_wit_edu/ergezerm_wit_edu-conda/envs/soft/bin:$PATH",
    "workdir": "$HOME/erdos_r3",
    # SLURM does not expand $HOME in #SBATCH --output/--error.  Keep this
    # relative to the submission directory, which should be $HOME/erdos_r3.
    "logdir": "results/slurm_logs",
    "chunk_time_limit": "60",
    "workers_per_chunk": "8",
    "array_throttle": "%200",  # at most 200 array tasks running at once
}


def parse_unknown_chunks(broad_path: Path, skip: set[int]) -> list[int]:
    rows = []
    with broad_path.open("r", encoding="utf-8") as fh:
        for ln in fh:
            ln = ln.strip()
            if not ln:
                continue
            rows.append(json.loads(ln))
    unk = sorted(
        r["chunk_id"] for r in rows
        if r.get("status") == "UNKNOWN" and r["chunk_id"] not in skip
    )
    return unk


def parse_chunk_list(path: Path) -> list[int]:
    text = path.read_text(encoding="utf-8").strip()
    if not text:
        return []
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        data = [
            token.strip()
            for token in text.replace(",", "\n").splitlines()
            if token.strip()
        ]
    if isinstance(data, dict):
        for key in ("chunk_ids", "chunks", "sample"):
            if key in data:
                data = data[key]
                break
        else:
            raise SystemExit(f"Could not find chunk list in {path}")
    return [int(value) for value in data]


def workdir_relative_path(path: Path) -> Path:
    """Return the path as it should appear relative to the Unity workdir."""
    if path.is_absolute():
        try:
            return path.resolve().relative_to(HERE)
        except ValueError:
            return Path(path.name)
    parts = path.parts
    if parts and parts[0] == HERE.name:
        return Path(*parts[1:])
    return path


def local_path(path: Path) -> Path:
    """Resolve a CLI path for local inspection from either repo root or erdos_r3."""
    if path.exists():
        return path
    candidate = HERE / path
    if candidate.exists():
        return candidate
    return path


def emit_phase1(args) -> None:
    skip = set()
    if args.skip_closed:
        skip = {int(x) for x in args.skip_closed.split(",") if x.strip()}
    if args.chunk_list:
        unk = parse_chunk_list(local_path(args.chunk_list))
        if skip:
            unk = [chunk_id for chunk_id in unk if chunk_id not in skip]
    else:
        unk = parse_unknown_chunks(local_path(args.broad), skip)
    if args.limit_unknowns is not None:
        unk = unk[:args.limit_unknowns]
    if not unk:
        print("No UNKNOWN chunks remain to refine.")
        return
    task_list = " ".join(str(c) for c in unk)
    n = len(unk)
    headers = dict(DEFAULTS)
    # Use the workdir-relative path inside the generated script.  This accepts
    # both `results/foo.jsonl` from inside erdos_r3 and `erdos_r3/results/foo`
    # from the repository root.
    broad_relative = workdir_relative_path(args.broad)
    headers.update({
        "nm1": str(n - 1),
        "task_list": task_list,
        "broad": f"{args.workdir}/{broad_relative}" if not str(broad_relative).startswith(args.workdir) else str(broad_relative),
        "partition": args.partition,
        "account": args.account,
        "time": args.time,
        "cpus": str(args.cpus),
        "mem": args.mem,
        "env_init": args.env_init or DEFAULTS["env_init"],
        "workdir": args.workdir,
        "logdir": args.logdir,
        "chunk_time_limit": str(args.chunk_time_limit),
        "workers_per_chunk": str(args.workers_per_chunk),
        "array_throttle": f"%{args.array_throttle}" if args.array_throttle else "",
        "refine_prefix": args.refine_prefix,
        "split_vars_name": args.split_vars_name,
        "hint_name": args.hint_name,
    })
    content = PHASE1_HEADER.format(**headers)
    args.out.write_text(content)
    print(f"Phase-1 SBATCH script written to {args.out}")
    print(f"  Task count: {n}")
    print(f"  Base chunk IDs: {unk}")
    print()
    print(f"Submit:  sbatch {args.out}")
    print(f"Monitor: squeue -u $USER -j <JOB_ID>")


def emit_phase2(args) -> None:
    if args.chunk_list:
        chunk_ids = parse_chunk_list(local_path(args.chunk_list))
        unique_ids = []
        seen_ids = set()
        for chunk_id in chunk_ids:
            if chunk_id not in seen_ids:
                seen_ids.add(chunk_id)
                unique_ids.append(chunk_id)
        if not unique_ids:
            raise SystemExit(f"No chunk IDs found in {args.chunk_list}")
        headers = dict(DEFAULTS)
        headers.update({
            "task_end": str(len(unique_ids) - 1),
            "chunk_ids": " ".join(str(chunk_id) for chunk_id in unique_ids),
            "partition": args.partition,
            "account": args.account,
            "time": args.time,
            "cpus": str(args.cpus),
            "mem": args.mem,
            "env_init": args.env_init or DEFAULTS["env_init"],
            "workdir": args.workdir,
            "logdir": args.logdir,
            "shard_dir": args.shard_dir,
            "chunk_time_limit": str(args.chunk_time_limit),
            "workers_per_chunk": str(args.workers_per_chunk),
            "array_throttle": f"%{args.array_throttle}" if args.array_throttle else "",
            "split_vars_name": args.split_vars_name,
            "hint_name": args.hint_name,
        })
        content = PHASE2_CHUNK_LIST_HEADER.format(**headers)
        args.out.write_text(content)
        print(f"Phase-2 chunk-list SBATCH script written to {args.out}")
        print(f"  Task count: {len(unique_ids)}")
        if len(unique_ids) != len(chunk_ids):
            print(f"  Deduplicated: {len(chunk_ids)} input IDs -> {len(unique_ids)} unique IDs")
        print()
        print("After completion, run:")
        print(f"  python3 r3_collect.py --shard-dir {args.shard_dir} \\")
        print(f"      --chunk-list {args.chunk_list} \\")
        print(f"      --out results/N212_K44_broad24_{args.out.stem}.jsonl")
        print()
        print(f"Submit:  sbatch {args.out}")
        return

    if args.chunk_start is None or args.chunk_end is None:
        raise SystemExit("--phase 2 requires --chunk-start and --chunk-end")
    if args.chunk_end <= args.chunk_start:
        raise SystemExit("--chunk-end must be > --chunk-start")
    headers = dict(DEFAULTS)
    chunks_per_task = args.chunks_per_task
    n_chunks = args.chunk_end - args.chunk_start
    n_tasks = (n_chunks + chunks_per_task - 1) // chunks_per_task
    headers.update({
        "start": str(args.chunk_start),
        "end": str(args.chunk_end - 1),
        "exclusive_end": str(args.chunk_end),
        "task_end": str(n_tasks - 1),
        "chunks_per_task": str(chunks_per_task),
        "partition": args.partition,
        "account": args.account,
        "time": args.time,
        "cpus": str(args.cpus),
        "mem": args.mem,
        "env_init": args.env_init or DEFAULTS["env_init"],
        "workdir": args.workdir,
        "logdir": args.logdir,
        "shard_dir": args.shard_dir,
        "chunk_time_limit": str(args.chunk_time_limit),
        "workers_per_chunk": str(args.workers_per_chunk),
        "array_throttle": f"%{args.array_throttle}" if args.array_throttle else "",
        "split_vars_name": args.split_vars_name,
        "hint_name": args.hint_name,
    })
    content = PHASE2_HEADER.format(**headers)
    args.out.write_text(content)
    print(f"Phase-2 SBATCH script written to {args.out}")
    print(f"  Chunk count: {n_chunks} ({args.chunk_start}..{args.chunk_end - 1})")
    print(f"  Chunks per task: {chunks_per_task}")
    print(f"  Array size: {n_tasks}")
    print()
    print(f"After completion, run:")
    print(f"  python3 r3_collect.py --shard-dir {args.shard_dir} \\")
    print(f"      --chunk-start {args.chunk_start} --chunk-end {args.chunk_end} \\")
    print(f"      --out results/N212_K44_broad24_{args.chunk_start}_{args.chunk_end - 1}.jsonl")
    print()
    print(f"Submit:  sbatch {args.out}")


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--phase", type=int, required=True, choices=[1, 2])
    p.add_argument("--out", type=Path, required=True)
    # Phase-1 args
    p.add_argument("--broad", type=Path, default=Path(
        "results/N212_K44_split_witness24_endpoints_pruned_600.jsonl"))
    p.add_argument("--skip-closed", type=str, default="31,63,95,126,127,159",
                   help="Comma-sep already-closed chunk IDs (default: those closed in prior session)")
    p.add_argument("--chunk-list", type=Path, default=None,
                   help="Optional explicit JSON/newline/comma list of base chunk IDs for phase 1.")
    p.add_argument("--limit-unknowns", type=int, default=None,
                   help="Optional cap on phase-1 UNKNOWN/task count after parsing.")
    p.add_argument("--refine-prefix", default="refine_N212_K44_witness24",
                   help="Phase-1 output file prefix under results/.")
    # Phase-2 args
    p.add_argument("--chunk-start", type=int)
    p.add_argument("--chunk-end", type=int,
                   help="exclusive upper bound on chunk IDs")
    p.add_argument("--chunks-per-task", type=int, default=100,
                   help="Phase-2 chunk IDs handled per SLURM array task")
    p.add_argument("--shard-dir", default="results/broad24",
                   help="Phase-2 shard output directory, relative to --workdir")
    # Shared SBATCH knobs
    p.add_argument("--partition", default=DEFAULTS["partition"])
    p.add_argument("--account", default=DEFAULTS["account"])
    p.add_argument("--time", default=DEFAULTS["time"])
    p.add_argument("--cpus", type=int, default=int(DEFAULTS["cpus"]))
    p.add_argument("--mem", default=DEFAULTS["mem"])
    p.add_argument("--env-init", default=None,
                   help="Override env-init shell snippet (default: try `module load conda` then activate r3)")
    p.add_argument("--workdir", default=DEFAULTS["workdir"])
    p.add_argument("--logdir", default=DEFAULTS["logdir"])
    p.add_argument("--chunk-time-limit", type=int, default=int(DEFAULTS["chunk_time_limit"]))
    p.add_argument("--workers-per-chunk", type=int, default=int(DEFAULTS["workers_per_chunk"]))
    p.add_argument("--array-throttle", type=int, default=200,
                   help="Max array tasks running concurrently (default: 200; 0 for unlimited)")
    p.add_argument("--split-vars-name", default="N212_K43_witness_degree_order.json",
                   help="Filename (under results/) of the split-vars JSON used by both phases")
    p.add_argument("--hint-name", default="N212_K43_witness.json",
                   help="Filename (under results/) of the witness JSON used as CP-SAT hint")
    args = p.parse_args()

    if args.phase == 1:
        emit_phase1(args)
    else:
        emit_phase2(args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
