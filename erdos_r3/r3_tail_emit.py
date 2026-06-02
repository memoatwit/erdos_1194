"""
Emit a Unity SLURM array for residual r_3 refinement tails.

This parses existing refinement JSONL files for rows with status UNKNOWN and
emits one array task per residual subchunk.  It supports any depth in the
refinement tree, including level-3 cleanup of depth-8 tail files.

Two modes for naming the parent JSONL passed to r3_split_cpsat:

  * Default (preferred): each input file IS the parent JSONL.  The emitted
    array task supplies that exact file path via PARENT_JSONL and the UNKNOWN
    row's chunk_id via PARENT_CHUNK_ID.  Works for any level of the tree.

  * Legacy prefix/suffix mode: the input files are scanned, then their base
    chunk id is plugged into `--parent-prefix${base}${parent-suffix}` to form
    the parent JSONL path.  Useful only when the parent file shares a common
    pattern with the input files.

Output JSONL naming:

  results/{out_prefix}_{parent_tag}_subchunk${PARENT_CHUNK_ID}_next{depth}_{cap}.jsonl

where parent_tag is captured from the input filename via --parent-tag-regex,
or defaults to the input basename minus extension.
"""
from __future__ import annotations

import argparse
import glob
import json
import re
from pathlib import Path


DEFAULT_ENV_INIT = (
    "export PATH=/work/pi_ergezerm_wit_edu/ergezerm_wit_edu-conda/envs/soft/bin:$PATH"
)


SBATCH_TEMPLATE = """#!/bin/bash
#SBATCH --job-name={job_name}
#SBATCH --partition={partition}
#SBATCH --account={account}
#SBATCH --time={time}
#SBATCH --array=0-{task_end}{array_throttle}
#SBATCH --cpus-per-task={cpus}
#SBATCH --mem={mem}
#SBATCH --output={logdir}/{job_name}-%A_%a.out
#SBATCH --error={logdir}/{job_name}-%A_%a.err

set -euo pipefail
{env_init}

cd {workdir}

PARENT_JSONLS=({parent_jsonls})
PARENT_CHUNK_IDS=({parent_chunk_ids})
PARENT_TAGS=({parent_tags})

PARENT_JSONL="${{PARENT_JSONLS[$SLURM_ARRAY_TASK_ID]}}"
PARENT_CHUNK_ID="${{PARENT_CHUNK_IDS[$SLURM_ARRAY_TASK_ID]}}"
PARENT_TAG="${{PARENT_TAGS[$SLURM_ARRAY_TASK_ID]}}"

OUT="{workdir}/results/{out_prefix}_${{PARENT_TAG}}_subchunk${{PARENT_CHUNK_ID}}_next{depth}_{chunk_time_limit}.jsonl"

if [ -s "$OUT" ]; then
  echo "[skip] $OUT already exists"
  exit 0
fi

python "{workdir}/r3_split_cpsat.py" \\
  --N 212 --K 44 \\
  --pairs {depth} \\
  --strategy degree-vars \\
  --split-count {depth} \\
  --split-vars "{workdir}/results/{split_vars_name}" \\
  --base-jsonl "$PARENT_JSONL" \\
  --base-chunk-id "$PARENT_CHUNK_ID" \\
  --chunk-time-limit {chunk_time_limit} \\
  --workers-per-chunk {workers_per_chunk} \\
  --hint "{workdir}/results/N212_K43_witness.json" \\
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


def derive_parent_tag(filename: str, tag_regex: re.Pattern | None) -> str:
    name = Path(filename).name
    if tag_regex is not None:
        m = tag_regex.search(name)
        if m and m.groups():
            return "_".join(g for g in m.groups() if g)
    # Fallback: basename without extension.
    return Path(name).stem


def parse_unknowns_per_file(
    input_paths: list[str],
    *,
    tag_regex: re.Pattern | None,
    parent_prefix: str | None,
    parent_suffix: str | None,
    legacy_base_regex: re.Pattern | None,
) -> list[tuple[str, int, str]]:
    """Return list of (parent_jsonl, parent_chunk_id, parent_tag) tuples."""
    out: list[tuple[str, int, str]] = []
    for filename in input_paths:
        parent_tag = derive_parent_tag(filename, tag_regex)
        if parent_prefix is not None and parent_suffix is not None:
            # Legacy mode: derive parent path from filename via base regex.
            if legacy_base_regex is None:
                raise SystemExit("Legacy parent-prefix/suffix mode requires --base-regex")
            base_match = legacy_base_regex.search(Path(filename).name)
            if not base_match:
                continue
            base_chunk_id = int(base_match.group(1))
            parent_path = f"{parent_prefix}{base_chunk_id}{parent_suffix}"
        else:
            # Preferred mode: each input file is its own parent.
            parent_path = filename
        with open(filename, "r", encoding="utf-8") as fh:
            for line in fh:
                if not line.strip():
                    continue
                row = json.loads(line)
                if row.get("status") == "UNKNOWN":
                    out.append((parent_path, int(row["chunk_id"]), parent_tag))
    # Dedupe while preserving order.
    seen = set()
    dedup: list[tuple[str, int, str]] = []
    for entry in out:
        key = (entry[0], entry[1])
        if key not in seen:
            seen.add(key)
            dedup.append(entry)
    return dedup


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-glob", required=True,
                        help="Glob for refinement JSONL files to scan for UNKNOWN rows.")
    parser.add_argument("--expected-files", type=int, default=None,
                        help="Abort unless the input glob matches exactly this many files.")
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--job-name", default="r3_tail")
    parser.add_argument("--out-prefix", default="refine_N212_K44_tail",
                        help="Prefix for emitted output JSONLs (under results/).")
    parser.add_argument("--parent-tag-regex", default=None,
                        help="Optional regex on input basename whose capture groups form the parent tag. "
                             "Default: input basename without extension.")
    parser.add_argument("--depth", type=int, default=8)
    parser.add_argument("--chunk-time-limit", type=int, default=60)
    parser.add_argument("--workers-per-chunk", type=int, default=8)
    parser.add_argument("--partition", default="cpu")
    parser.add_argument("--account", default="pi_ergezerm_wit_edu")
    parser.add_argument("--time", default="02:00:00")
    parser.add_argument("--cpus", type=int, default=8)
    parser.add_argument("--mem", default="8G")
    parser.add_argument("--workdir", default="$HOME/erdos_r3")
    parser.add_argument("--logdir", default="results/slurm_logs")
    parser.add_argument("--array-throttle", type=int, default=75)
    parser.add_argument("--env-init", default=DEFAULT_ENV_INIT)
    parser.add_argument("--split-vars-name", default="N212_K43_witness_degree_order.json")
    # Legacy mode for backward compatibility:
    parser.add_argument("--parent-prefix", default=None,
                        help="Legacy mode: prefix template for parent JSONL path.")
    parser.add_argument("--parent-suffix", default=None,
                        help="Legacy mode: suffix template for parent JSONL path.")
    parser.add_argument("--base-regex",
                        default=r"chunk([0-9]+)_next[0-9]+_[0-9]+\.jsonl$",
                        help="Legacy mode: regex whose first capture group is the parent base chunk id.")
    args = parser.parse_args()

    tag_regex = re.compile(args.parent_tag_regex) if args.parent_tag_regex else None
    legacy_base_regex = re.compile(args.base_regex) if args.parent_prefix else None

    files = sorted(glob.glob(args.input_glob))
    if args.expected_files is not None and len(files) != args.expected_files:
        raise SystemExit(
            f"Expected {args.expected_files} files for {args.input_glob}, found {len(files)}."
        )

    triples = parse_unknowns_per_file(
        files,
        tag_regex=tag_regex,
        parent_prefix=args.parent_prefix,
        parent_suffix=args.parent_suffix,
        legacy_base_regex=legacy_base_regex,
    )
    if not triples:
        print(json.dumps({
            "input_glob": args.input_glob,
            "matched_files": len(files),
            "tail_count": 0,
            "message": "No UNKNOWN tail rows found; no SBATCH emitted.",
        }, indent=2))
        return 0

    # Quote parent paths so spaces / special chars are safe inside the bash array.
    def q(s: str) -> str:
        if any(ch in s for ch in " \t\"'$"):
            esc = s.replace("\"", "\\\"")
            return f"\"{esc}\""
        return s

    parent_jsonls = " ".join(q(p) for p, _, _ in triples)
    parent_chunk_ids = " ".join(str(c) for _, c, _ in triples)
    parent_tags = " ".join(q(t) for _, _, t in triples)

    content = SBATCH_TEMPLATE.format(
        job_name=args.job_name,
        partition=args.partition,
        account=args.account,
        time=args.time,
        task_end=len(triples) - 1,
        array_throttle=f"%{args.array_throttle}" if args.array_throttle else "",
        cpus=args.cpus,
        mem=args.mem,
        logdir=args.logdir,
        env_init=args.env_init,
        workdir=args.workdir,
        parent_jsonls=parent_jsonls,
        parent_chunk_ids=parent_chunk_ids,
        parent_tags=parent_tags,
        out_prefix=args.out_prefix,
        depth=args.depth,
        chunk_time_limit=args.chunk_time_limit,
        workers_per_chunk=args.workers_per_chunk,
        split_vars_name=args.split_vars_name,
    )
    args.out.write_text(content, encoding="utf-8")
    print(json.dumps({
        "input_glob": args.input_glob,
        "matched_files": len(files),
        "out": str(args.out),
        "tail_count": len(triples),
        "tails": [
            {"parent_jsonl": p, "parent_chunk_id": c, "parent_tag": t}
            for p, c, t in triples
        ],
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
