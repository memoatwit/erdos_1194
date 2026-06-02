#!/usr/bin/env python3
"""Assemble the r_3(212) Zenodo artifact bundle.

The campaign workspace is large, so this script hardlinks large artifacts into
the release directory whenever source and destination are on the same
filesystem. That gives Zenodo a clean upload tree without doubling disk usage.

Default usage on Unity:

    cd /work/pi_ergezerm_wit_edu/ergezerm_wit_edu/erdos_r3
    python zenodo/build_zenodo_bundle.py

Output:

    /work/pi_ergezerm_wit_edu/ergezerm_wit_edu/r3-212-campaign-v1
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Iterable


T1C = {40959, 48895}
T1B_MINUS_T1C = {
    14331,
    15357,
    24557,
    32251,
    32637,
    32735,
    36859,
    40943,
    63231,
    64319,
    65373,
    77311,
    81279,
    89838,
    93949,
    97782,
    110586,
    110587,
}
PROOF_CHUNKS = sorted(T1B_MINUS_T1C)


def relink_or_copy(src: Path, dst: Path) -> None:
    """Hardlink src to dst when possible; fall back to copy2."""
    if not src.exists():
        raise FileNotFoundError(src)
    dst.parent.mkdir(parents=True, exist_ok=True)
    if dst.exists():
        return
    try:
        os.link(src, dst)
    except OSError:
        shutil.copy2(src, dst)


def copy_tree_files(src_dir: Path, dst_dir: Path, patterns: Iterable[str] = ("*",)) -> None:
    if not src_dir.exists():
        return
    for pattern in patterns:
        for src in sorted(src_dir.glob(pattern)):
            if src.is_file():
                relink_or_copy(src, dst_dir / src.name)


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w") as fh:
        for row in rows:
            fh.write(json.dumps(row, sort_keys=True) + "\n")


def load_jsonl(path: Path) -> list[dict]:
    rows = []
    with path.open() as fh:
        for line in fh:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def build_tier_files(root: Path, bundle: Path) -> None:
    residual_path = root / "results/N212_K44_broad24_recap300_residual45.jsonl"
    highs_dir = root / "results/highs_t1_longwall45"
    residual_rows = {int(r["chunk_id"]): r for r in load_jsonl(residual_path)}

    t1a_ids: set[int] = set()
    t1b_ids: set[int] = set()
    for p in sorted(highs_dir.glob("*.jsonl")):
        for row in load_jsonl(p):
            cid = int(row["chunk_id"])
            if row.get("status") == "INFEASIBLE":
                t1a_ids.add(cid)
            elif row.get("status") == "UNKNOWN":
                t1b_ids.add(cid)

    if len(t1a_ids) != 25:
        raise RuntimeError(f"expected 25 T1a chunks, found {len(t1a_ids)}")
    if len(t1b_ids) != 20:
        raise RuntimeError(f"expected 20 T1b chunks, found {len(t1b_ids)}")
    if not T1C.issubset(t1b_ids):
        raise RuntimeError(f"T1c not subset of T1b: {T1C - t1b_ids}")
    if set(T1B_MINUS_T1C) != (t1b_ids - T1C):
        raise RuntimeError("hard-coded T1b\\T1c set does not match HiGHS audit")

    def rows_for(ids: Iterable[int], tier: str) -> list[dict]:
        out = []
        for cid in sorted(ids):
            row = dict(residual_rows[cid])
            row["benchmark_tier"] = tier
            out.append(row)
        return out

    small = bundle / "small"
    write_jsonl(small / "N212_K44_t1a25.jsonl", rows_for(t1a_ids, "T1a"))
    write_jsonl(
        small / "N212_K44_t1b_minus_t1c.jsonl",
        rows_for(T1B_MINUS_T1C, "T1b_minus_T1c"),
    )
    write_jsonl(small / "N212_K44_t1c2.jsonl", rows_for(T1C, "T1c"))


def collect_small_files(root: Path, bundle: Path) -> None:
    small = bundle / "small"
    for rel in [
        "results/N212_K43_witness.json",
        "results/N212_K44_force_endpoints.json",
        "results/N212_K44_window100k_unknowns.jsonl",
        "results/b003002.txt",
    ]:
        src = root / rel
        relink_or_copy(src, small / src.name)
    # Include the full 45-row residual as provenance for the T1 split.
    relink_or_copy(
        root / "results/N212_K44_broad24_recap300_residual45.jsonl",
        small / "N212_K44_broad24_recap300_residual45.jsonl",
    )


def collect_lean(root: Path, bundle: Path) -> None:
    copy_tree_files(root / "lean", bundle / "lean", ("*.lean", "*.md", "*.sh"))


def collect_code(root: Path, bundle: Path) -> None:
    code = bundle / "code"
    for name in [
        "r3_sat_attack.py",
        "verify_t1b_proofs.py",
        "aggregate_verifications.py",
        "r3_verify.py",
        "r3_split_cpsat.py",
        "r3_cpsat.py",
        "r3_highs_attack.py",
        "r3_collect.py",
        "build_drat_trim.sh",
    ]:
        relink_or_copy(root / name, code / name)


def collect_proofs(root: Path, bundle: Path) -> None:
    proof_root = bundle / "sat_t1b_proofs"
    relink_or_copy(
        root / "results/sat_t1b_proofs/verification_all.jsonl",
        proof_root / "verification_all.jsonl",
    )
    relink_or_copy(
        root / "results/sat_t1b_proofs/verification_summary_final.json",
        proof_root / "verification_summary_final.json",
    )

    for cid in PROOF_CHUNKS:
        if cid == 32735:
            src_dir = root / "results/sat_t1b_proof32735_64g/scratch"
        else:
            src_dir = root / "results/sat_t1b_proofs/scratch"
        for suffix in [".cnf", ".drat"]:
            src = src_dir / f"chunk_{cid:08d}{suffix}"
            relink_or_copy(src, proof_root / ("cnf" if suffix == ".cnf" else "drat") / src.name)

    # Actual LRAT (-L) artifacts exist for the final two verifier tasks.
    for cid in [32735, 63231]:
        src = root / "results/sat_t1b_proofs/lrat_final2_24h" / f"chunk_{cid:08d}.lrat"
        relink_or_copy(src, proof_root / "lrat_final2_24h" / src.name)


def collect_logs(root: Path, bundle: Path) -> None:
    logs = bundle / "logs"
    copy_tree_files(root / "results/slurm_logs", logs / "slurm_logs", ("*.out", "*.err"))
    for name in [
        "highs45",
        "highs_t1_longwall45",
        "sat_t1b",
        "sat_t1b_proofs",
        "sat_t1b_proof32735_64g",
        "sat_t1c_diag",
    ]:
        src_dir = root / "results" / name
        dst_dir = logs / name
        # Keep logs JSONL, not the giant CNF/DRAT scratch trees duplicated here.
        copy_tree_files(src_dir, dst_dir, ("*.jsonl", "*.json"))


def collect_environment(root: Path, bundle: Path) -> None:
    env = bundle / "environment"
    env.mkdir(parents=True, exist_ok=True)

    def run(cmd: list[str]) -> str:
        try:
            return subprocess.run(cmd, capture_output=True, text=True, check=False).stdout
        except OSError as exc:
            return f"{cmd[0]} unavailable: {exc}\n"

    (env / "unity_versions.txt").write_text(
        "python:\n"
        + run([sys.executable, "--version"])
        + "\nsha256sum:\n"
        + run(["sha256sum", "--version"])
        + "\ndrat-trim:\n"
        + run([str(root / "drat-trim")])
    )
    (env / "python_packages.txt").write_text(run([sys.executable, "-m", "pip", "freeze"]))
    (env / "slurm_jobs.tsv").write_text(
        run(
            [
                "sacct",
                "-j",
                "58782313,58832970,58913424,58913425,58952708,59058393,59058394,59155561,59155562,59383874",
                "--format=JobID,JobName%32,State,Elapsed,MaxRSS,ReqMem,ExitCode",
                "-P",
            ]
        )
    )


def write_manifest(bundle: Path) -> None:
    manifest = bundle / "MANIFEST.sha256"
    entries: list[tuple[str, str]] = []
    for path in sorted(p for p in bundle.rglob("*") if p.is_file() and p.name != "MANIFEST.sha256"):
        h = hashlib.sha256()
        with path.open("rb") as fh:
            for chunk in iter(lambda: fh.read(1024 * 1024), b""):
                h.update(chunk)
        rel = path.relative_to(bundle).as_posix()
        entries.append((h.hexdigest(), rel))
    with manifest.open("w") as fh:
        for digest, rel in entries:
            fh.write(f"{digest}  {rel}\n")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", type=Path, default=Path.cwd())
    ap.add_argument("--bundle", type=Path, default=None)
    ap.add_argument("--no-manifest", action="store_true")
    args = ap.parse_args()

    root = args.root.resolve()
    bundle = (
        args.bundle.resolve()
        if args.bundle is not None
        else root.parent / "r3-212-campaign-v1"
    )
    bundle.mkdir(parents=True, exist_ok=True)

    relink_or_copy(root / "zenodo/README.md", bundle / "README.md")
    collect_small_files(root, bundle)
    build_tier_files(root, bundle)
    collect_lean(root, bundle)
    collect_code(root, bundle)
    collect_proofs(root, bundle)
    collect_logs(root, bundle)
    collect_environment(root, bundle)

    if not args.no_manifest:
        write_manifest(bundle)

    print(f"[done] bundle: {bundle}")
    print(f"[done] size:")
    subprocess.run(["du", "-sh", str(bundle)], check=False)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
