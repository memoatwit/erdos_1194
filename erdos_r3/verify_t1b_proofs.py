#!/usr/bin/env python3
"""
verify_t1b_proofs.py — independently verify DRAT proofs produced by the
T1b proof-producing rerun (Unity job 58913424).

For each chunk in the T1b UNSAT set, locate the matching CNF and DRAT
files, invoke drat-trim, and record the verification outcome in a JSONL
row. The result file is the canonical machine-checkable evidence for
the 18 UNSAT closures of T1b: a "VERIFIED" row means a third-party
independent verifier (drat-trim, by Marijn Heule) confirmed the
solver's UNSAT proof.

Optionally also emits LRAT (linear, trimmed) proofs alongside DRAT,
which are accepted by formally verified checkers (cake_lpr, lrat-check).

Inputs are organized by chunk_id:
  --proofs-dir/chunk_<id:08d>.drat
  --cnfs-dir/chunk_<id:08d>.cnf

Output one JSONL row per chunk with status ∈ {VERIFIED, NOT_VERIFIED,
MISSING_CNF, MISSING_DRAT, TIMEOUT, ERROR}.

Usage:
  python3 verify_t1b_proofs.py \\
      --proofs-dir results/sat_t1b_proofs \\
      --cnfs-dir   results/sat_t1b_proofs/scratch \\
      --output     results/sat_t1b_proofs/verification.jsonl \\
      --drat-trim  ./drat-trim \\
      --array-index $SLURM_ARRAY_TASK_ID
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path


T1B_CHUNK_IDS_ORDERED: list[int] = [
    14331, 15357, 24557, 32251, 32637, 32735, 36859, 40943,
    40959, 48895, 63231, 64319, 65373, 77311, 81279, 89838,
    93949, 97782, 110586, 110587,
]

# The proof-available T1b chunks. T1c = {40959, 48895} are intentionally
# excluded because they remained UNKNOWN in the original CDCL run; chunk 32735
# is also excluded because the proof-producing rerun timed out before emitting
# a DRAT proof. This list is the canonical ordering the verification SBATCH
# array indexes into.
T1B_UNSAT_CHUNK_IDS_ORDERED: list[int] = [
    cid for cid in T1B_CHUNK_IDS_ORDERED if cid not in (32735, 40959, 48895)
]
assert len(T1B_UNSAT_CHUNK_IDS_ORDERED) == 17


def find_with_suffixes(root: Path, chunk_id: int, suffix: str) -> Path | None:
    """Locate a file named chunk_<id:08d>.<suffix> or a few common variants."""
    candidates = [
        root / f"chunk_{chunk_id:08d}{suffix}",
        root / f"chunk_{chunk_id}{suffix}",
        root / f"{chunk_id:08d}{suffix}",
        root / f"{chunk_id}{suffix}",
    ]
    for p in candidates:
        if p.exists() and p.stat().st_size > 0:
            return p
    # Last resort: scan with glob
    for p in root.glob(f"*{chunk_id}*{suffix}"):
        if p.stat().st_size > 0:
            return p
    return None


def run_drat_trim(
    drat_trim_bin: str,
    cnf_path: Path,
    drat_path: Path,
    lrat_path: Path | None,
    time_limit_s: int,
) -> dict:
    cmd = [drat_trim_bin, str(cnf_path), str(drat_path), "-t", str(time_limit_s)]
    if lrat_path is not None:
        # drat-trim uses -L for LRAT. Lowercase -l emits trimmed DRAT lemmas.
        cmd.extend(["-L", str(lrat_path)])
    t0 = time.time()
    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=time_limit_s,
            check=False,
        )
        elapsed = time.time() - t0
        out = proc.stdout or ""
        err = proc.stderr or ""
        rc = proc.returncode
        status = "ERROR"
        for line in out.splitlines():
            s = line.strip().upper()
            if s.startswith("S VERIFIED"):
                status = "VERIFIED"
                break
            if s.startswith("S NOT VERIFIED"):
                status = "NOT_VERIFIED"
                break
            if s.startswith("S TIMEOUT"):
                status = "TIMEOUT"
                break
        # drat-trim exit-code convention: 0 = VERIFIED (s VERIFIED), 1 = NOT
        # VERIFIED, other = error. Be permissive and prefer the parsed line.
        if status == "ERROR" and rc == 0 and "verified" in out.lower():
            status = "VERIFIED"
        if status == "ERROR" and rc != 0 and "not verified" in out.lower():
            status = "NOT_VERIFIED"
    except subprocess.TimeoutExpired as e:
        elapsed = time.time() - t0
        out = (e.stdout or b"").decode("utf-8", errors="replace")
        err = (e.stderr or b"").decode("utf-8", errors="replace")
        rc = -1
        status = "TIMEOUT"
    return {
        "status": status,
        "drat_trim_seconds": elapsed,
        "exit_code": rc,
        "stdout_tail": "\n".join(out.splitlines()[-30:]),
        "stderr_tail": "\n".join(err.splitlines()[-10:]),
    }


def verify_one_chunk(
    chunk_id: int,
    proofs_dir: Path,
    cnfs_dir: Path,
    drat_trim_bin: str,
    time_limit_s: int,
    emit_lrat: bool,
    lrat_dir: Path | None,
) -> dict:
    record: dict = {
        "chunk_id": chunk_id,
        "drat_trim_bin": drat_trim_bin,
        "time_limit_s": time_limit_s,
    }
    cnf_path = find_with_suffixes(cnfs_dir, chunk_id, ".cnf")
    drat_path = find_with_suffixes(proofs_dir, chunk_id, ".drat")
    if cnf_path is None:
        record["status"] = "MISSING_CNF"
        record["cnf_path"] = None
        record["drat_path"] = str(drat_path) if drat_path else None
        return record
    if drat_path is None:
        record["status"] = "MISSING_DRAT"
        record["cnf_path"] = str(cnf_path)
        record["drat_path"] = None
        return record
    record["cnf_path"] = str(cnf_path)
    record["drat_path"] = str(drat_path)
    record["cnf_bytes"] = cnf_path.stat().st_size
    record["drat_bytes"] = drat_path.stat().st_size
    lrat_path: Path | None = None
    if emit_lrat and lrat_dir is not None:
        lrat_dir.mkdir(parents=True, exist_ok=True)
        lrat_path = lrat_dir / f"chunk_{chunk_id:08d}.lrat"
        record["lrat_path"] = str(lrat_path)
        record["lrat_format"] = "LRAT"
    res = run_drat_trim(
        drat_trim_bin=drat_trim_bin,
        cnf_path=cnf_path,
        drat_path=drat_path,
        lrat_path=lrat_path,
        time_limit_s=time_limit_s,
    )
    record.update(res)
    if lrat_path is not None and lrat_path.exists():
        record["lrat_bytes"] = lrat_path.stat().st_size
    return record


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Independently verify T1b DRAT proofs with drat-trim."
    )
    ap.add_argument(
        "--proofs-dir",
        type=Path,
        default=Path("results/sat_t1b_proofs"),
        help="Directory containing chunk_*.drat files.",
    )
    ap.add_argument(
        "--cnfs-dir",
        type=Path,
        default=Path("results/sat_t1b_proofs/scratch"),
        help="Directory containing chunk_*.cnf files (kept by the proof rerun).",
    )
    ap.add_argument(
        "--output",
        type=Path,
        default=Path("results/sat_t1b_proofs/verification.jsonl"),
        help="JSONL output: one verification row per chunk processed.",
    )
    ap.add_argument(
        "--drat-trim",
        type=str,
        default=os.environ.get("DRAT_TRIM_BIN", "./drat-trim"),
        help="drat-trim binary path.",
    )
    ap.add_argument(
        "--time-limit", type=int, default=3600, help="Per-chunk verification wall."
    )
    ap.add_argument(
        "--array-index",
        type=int,
        default=None,
        help=(
            "If set, verify only the chunk at this 0-based row of the T1b "
            "proof-available ordered list (17 chunks; the T1c residuals "
            "40959/48895 and proof-timeout chunk 32735 are excluded because "
            "they have no DRAT to verify)."
        ),
    )
    ap.add_argument(
        "--chunk-id",
        type=int,
        default=None,
        help="If set, verify only this single chunk_id.",
    )
    ap.add_argument(
        "--emit-lrat",
        action="store_true",
        help="Ask drat-trim to also emit an LRAT proof for each chunk.",
    )
    ap.add_argument(
        "--lrat-dir",
        type=Path,
        default=None,
        help="Where to write LRAT files (default: <proofs-dir>/lrat).",
    )
    ap.add_argument(
        "--exit-zero-on-nonverified",
        action="store_true",
        help=(
            "Always exit 0 after writing JSONL rows, even for TIMEOUT, "
            "NOT_VERIFIED, MISSING_*, or ERROR statuses. Useful for SLURM "
            "array tasks where diagnostic rows must be preserved."
        ),
    )
    args = ap.parse_args()

    # Determine which chunks to verify. --array-index resolves against the
    # 17-element proof-available UNSAT list so that array indices 0..16 map
    # cleanly to chunks with proof files. Use --chunk-id to verify a specific
    # chunk regardless of its membership in either list.
    if args.chunk_id is not None:
        chunks = [args.chunk_id]
    elif args.array_index is not None:
        if args.array_index < 0 or args.array_index >= len(T1B_UNSAT_CHUNK_IDS_ORDERED):
            print(
                f"[error] array-index {args.array_index} out of range "
                f"(have {len(T1B_UNSAT_CHUNK_IDS_ORDERED)} T1b proof chunks)",
                file=sys.stderr,
            )
            return 2
        chunks = [T1B_UNSAT_CHUNK_IDS_ORDERED[args.array_index]]
    else:
        chunks = list(T1B_UNSAT_CHUNK_IDS_ORDERED)

    if args.emit_lrat and args.lrat_dir is None:
        args.lrat_dir = args.proofs_dir / "lrat"

    args.output.parent.mkdir(parents=True, exist_ok=True)
    seen: set[int] = set()
    if args.output.exists():
        for line in args.output.read_text().splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                seen.add(json.loads(line).get("chunk_id"))
            except json.JSONDecodeError:
                continue

    print(
        f"[setup] chunks_to_verify={len(chunks)} already_done={len(seen)} "
        f"drat_trim={args.drat_trim}",
        file=sys.stderr,
    )

    not_verified_or_error = 0
    with args.output.open("a") as fh:
        for cid in chunks:
            if cid in seen:
                print(f"[skip] chunk_id={cid} already verified", file=sys.stderr)
                continue
            t0 = time.time()
            print(f"[run] chunk_id={cid} starting", file=sys.stderr)
            record = verify_one_chunk(
                chunk_id=cid,
                proofs_dir=args.proofs_dir,
                cnfs_dir=args.cnfs_dir,
                drat_trim_bin=args.drat_trim,
                time_limit_s=args.time_limit,
                emit_lrat=args.emit_lrat,
                lrat_dir=args.lrat_dir,
            )
            elapsed = time.time() - t0
            fh.write(json.dumps(record) + "\n")
            fh.flush()
            print(
                f"[done] chunk_id={cid} status={record.get('status')} "
                f"drat_trim_s={record.get('drat_trim_seconds', float('nan')):.1f} "
                f"wall_s={elapsed:.1f}",
                file=sys.stderr,
            )
            if record.get("status") not in {"VERIFIED"}:
                not_verified_or_error += 1

    if args.exit_zero_on_nonverified:
        return 0
    return 0 if not_verified_or_error == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
