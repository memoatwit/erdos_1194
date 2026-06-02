#!/usr/bin/env python3
"""
r3_sat_attack.py — CDCL/SAT attack on T1b residual chunks for r_3(212) <= 43.

Encodes a single broad chunk of the r_3(N, K) decision problem as a CNF
instance, invokes a CDCL solver (Kissat by default) with DRAT proof
logging when an external proof-producing solver is used, and writes a JSONL
row with status, solver time, and proof path when available. Designed as the
third-paradigm attack on the T1b hard core that
both CP-SAT (constraint propagation) and HiGHS (LP-relaxation MIP) failed
to close: CDCL/SAT has no LP-dual concept and may find the contradiction
via conflict-driven clause learning.

Encoding:
  Variables: x_1 ... x_N for membership in [1, N].
  Auxiliaries: created automatically by the cardinality encodings.
  Clauses:
    * Every 3-AP triple (a, b, c) gives the binary clause
        (¬x_a ∨ ¬x_b ∨ ¬x_c).
    * Every window-cardinality bound sum_{i in W} x_i ≤ r_3(L) is
      encoded via PySAT's sequential-counter (Sinz 2005) at-most-K.
    * The cardinality equality sum_i x_i = K is encoded as the pair
      (sum_i x_i ≤ K) ∧ (sum_i x_i ≥ K), via PySAT's totalizer at-most-K
      and at-least-K respectively (totalizer keeps the cardinality
      auxiliaries shared between the two directions).
    * Endpoint forcing x_1 = 1 and x_N = 1 as unit clauses (when N == 212).
    * fixed_in / fixed_out from the chunk row as unit clauses.

Output: a JSONL row {chunk_id, status, seconds, encode_seconds,
solver_seconds, n_vars, n_clauses, proof_path, exit_code, ...} where
status ∈ {SAT, UNSAT, UNKNOWN}.

Dependencies:
  * Python 3.10+
  * pip install python-sat   (PySAT, provides CardEnc)
  * kissat binary on PATH (or pass --solver-binary). Use
    --solver-binary pysat:auto for a portable no-certificate fallback.

Author: erdos_r3 campaign.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Any, Iterable

try:
    from pysat.card import CardEnc, EncType
    from pysat.formula import CNF, IDPool
    from pysat.solvers import Solver
except ImportError as exc:
    sys.stderr.write(
        "ERROR: PySAT not installed. Run: pip install python-sat[aiger,approxmc,cryptosat,pblib]\n"
    )
    raise


# ---------------------------------------------------------------------------
# Problem assembly
# ---------------------------------------------------------------------------


def enumerate_3ap_triples(N: int) -> list[tuple[int, int, int]]:
    """All (a, b, c) with 1 ≤ a < b < c ≤ N and b - a = c - b."""
    triples: list[tuple[int, int, int]] = []
    for a in range(1, N + 1):
        for d in range(1, (N - a) // 2 + 1):
            triples.append((a, a + d, a + 2 * d))
    return triples


def load_window_bounds(b_file: Path) -> dict[int, int]:
    """
    Read the OEIS A003002 b-file and return {L: r_3(L)} for L >= 1.
    The b-file format is one "L r_3(L)" pair per line.
    """
    out: dict[int, int] = {}
    with b_file.open() as fh:
        for line in fh:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split()
            if len(parts) < 2:
                continue
            L = int(parts[0])
            r = int(parts[1])
            out[L] = r
    return out


def build_window_constraints(
    N: int,
    K: int,
    r3: dict[int, int],
    length_filter: set[int] | None = None,
) -> list[tuple[list[int], int]]:
    """
    For each window [a, a+L-1] subset of [1,N] and each L with r_3(L) < min(L, K),
    emit (variables, k) representing the constraint sum_{i in window} x_i <= k.
    If length_filter is given, only emit constraints for L in length_filter.
    """
    constraints: list[tuple[list[int], int]] = []
    for L, k in sorted(r3.items()):
        if L > N or L < 3:
            continue
        if k >= min(L, K):
            continue
        if length_filter is not None and L not in length_filter:
            continue
        for a in range(1, N - L + 2):
            window_vars = list(range(a, a + L))
            constraints.append((window_vars, k))
    return constraints


def encode_chunk_as_cnf(
    N: int,
    K: int,
    fixed_in: Iterable[int],
    fixed_out: Iterable[int],
    triples: list[tuple[int, int, int]],
    window_constraints: list[tuple[list[int], int]],
    force_endpoints: bool = True,
) -> tuple[CNF, dict[str, int]]:
    """
    Returns (cnf, stats) where cnf is the PySAT CNF object and stats is a
    summary of the encoding sizes.
    """
    cnf = CNF()
    vpool = IDPool(start_from=N + 1)  # main vars are 1..N, aux start above

    # 3-AP clauses: not all three of x_a, x_b, x_c can be 1
    for a, b, c in triples:
        cnf.append([-a, -b, -c])

    # Window-cardinality constraints (at-most-k)
    # Sequential-counter (Sinz 2005) is the smallest standard encoding for
    # at-most-k when k is small relative to L; PySAT's totalizer is a strong
    # alternative when k is moderate. We default to seqcounter since most
    # window constraints have k ≪ L, but allow override via the env var
    # R3_SAT_WINDOW_ENC ∈ {seqcounter, totalizer, cardnetwk, ladder}.
    enc_name = os.environ.get("R3_SAT_WINDOW_ENC", "seqcounter")
    enc_map = {
        "seqcounter": EncType.seqcounter,
        "totalizer": EncType.totalizer,
        "cardnetwk": EncType.cardnetwrk,
        "ladder": EncType.ladder,
    }
    window_enc = enc_map.get(enc_name, EncType.seqcounter)
    for window_vars, k in window_constraints:
        cnf.extend(
            CardEnc.atmost(
                lits=window_vars, bound=k, vpool=vpool, encoding=window_enc
            ).clauses
        )

    # Cardinality equality sum_i x_i = K, encoded as <= K and >= K.
    all_vars = list(range(1, N + 1))
    cnf.extend(
        CardEnc.atmost(
            lits=all_vars, bound=K, vpool=vpool, encoding=EncType.totalizer
        ).clauses
    )
    cnf.extend(
        CardEnc.atleast(
            lits=all_vars, bound=K, vpool=vpool, encoding=EncType.totalizer
        ).clauses
    )

    # Endpoint forcing
    if force_endpoints and N == 212:
        cnf.append([1])  # x_1 = 1
        cnf.append([N])  # x_212 = 1

    # Chunk pins
    for v in fixed_in:
        cnf.append([v])
    for v in fixed_out:
        cnf.append([-v])

    stats = {
        "n_vars": vpool.top,
        "n_clauses": len(cnf.clauses),
        "n_3ap_triples": len(triples),
        "n_window_constraints": len(window_constraints),
    }
    return cnf, stats


# ---------------------------------------------------------------------------
# Solver invocation
# ---------------------------------------------------------------------------


def run_solver(
    cnf: CNF,
    cnf_path: Path,
    proof_path: Path,
    solver_binary: str,
    time_limit_s: int,
    extra_args: list[str],
    pysat_with_proof: bool,
) -> dict[str, Any]:
    """
    Invoke the CDCL solver. Returns dict with status, solver_seconds, exit_code,
    stdout_tail, stderr_tail.

    solver_binary may be either an external Kissat-style binary or
    "pysat:<name>" for an in-process PySAT backend. Use "pysat:auto" to try a
    small preference list of bundled solvers. The PySAT backend is intended as
    a portable fallback on clusters without a standalone Kissat binary. Pass
    pysat_with_proof=True to request proof logging from PySAT solvers that
    support it.
    """
    if solver_binary.startswith("pysat:"):
        return run_pysat_solver(
            cnf_path=cnf_path,
            proof_path=proof_path,
            solver_name=solver_binary.split(":", 1)[1],
            time_limit_s=time_limit_s,
            with_proof=pysat_with_proof,
        )

    cmd = [solver_binary]
    cmd.extend(extra_args)
    cmd.extend([f"--time={time_limit_s}"])  # kissat-style time limit
    cmd.append(str(cnf_path))
    cmd.append(str(proof_path))

    t0 = time.time()
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=time_limit_s + 60,  # hard kill 1m past solver's own timer
            check=False,
        )
        elapsed = time.time() - t0
        out = result.stdout or ""
        err = result.stderr or ""
        exit_code = result.returncode
    except subprocess.TimeoutExpired as e:
        elapsed = time.time() - t0
        out = (e.stdout or b"").decode("utf-8", errors="replace")
        err = (e.stderr or b"").decode("utf-8", errors="replace")
        exit_code = -1

    # Parse Kissat-style "s SATISFIABLE" / "s UNSATISFIABLE" / "s UNKNOWN"
    status = "UNKNOWN"
    for line in out.splitlines():
        line = line.strip()
        if line.startswith("s "):
            tok = line.split()[1].upper() if len(line.split()) >= 2 else ""
            if tok == "SATISFIABLE":
                status = "SAT"
            elif tok == "UNSATISFIABLE":
                status = "UNSAT"
            elif tok == "UNKNOWN":
                status = "UNKNOWN"
            break

    return {
        "status": status,
        "solver_seconds": elapsed,
        "exit_code": exit_code,
        "stdout_tail": "\n".join(out.splitlines()[-30:]),
        "stderr_tail": "\n".join(err.splitlines()[-10:]),
    }


def choose_pysat_solver(name: str, with_proof: bool = False) -> str:
    """Return a usable PySAT solver name, expanding the portable 'auto' alias."""
    if name == "auto" and with_proof:
        # In the Unity python-sat wheel, Glucose emits non-empty proof traces
        # through PySAT; CaDiCaL solves but returns an empty proof list.
        candidates = ["glucose4", "glucose3", "cadical195", "cadical153", "cadical103"]
    elif name == "auto":
        candidates = ["cadical195", "cadical153", "cadical103", "glucose4", "glucose3", "minisat22"]
    else:
        candidates = [name]
    errors: list[str] = []
    for candidate in candidates:
        try:
            with Solver(name=candidate, with_proof=with_proof):
                return candidate
        except Exception as exc:  # PySAT raises different errors by backend/version.
            errors.append(f"{candidate}: {exc}")
    raise RuntimeError("No usable PySAT solver found; tried " + "; ".join(errors))


def run_pysat_solver(
    cnf_path: Path,
    proof_path: Path,
    solver_name: str,
    time_limit_s: int,
    with_proof: bool,
) -> dict[str, Any]:
    """Run a PySAT solver in a child process with an OS-level wall timeout."""
    t0 = time.time()
    stdout_lines: list[str] = []
    status = "UNKNOWN"
    exit_code = 0
    stats: dict[str, Any] = {}
    stderr = ""

    try:
        chosen = choose_pysat_solver(solver_name, with_proof=with_proof)
        worker = r"""
import json
import sys
from pysat.formula import CNF
from pysat.solvers import Solver

solver_name = sys.argv[1]
cnf_path = sys.argv[2]
proof_path = sys.argv[3]
with_proof = sys.argv[4] == "1"
cnf = CNF(from_file=cnf_path)
proof_len = None
proof_written = False
with Solver(name=solver_name, with_proof=with_proof, bootstrap_with=cnf.clauses) as solver:
    sat = solver.solve()
    try:
        stats = dict(solver.accum_stats())
    except Exception:
        stats = {}
    status = "SAT" if sat is True else ("UNSAT" if sat is False else "UNKNOWN")
    if with_proof and status == "UNSAT":
        proof = solver.get_proof()
        proof_len = None if proof is None else len(proof)
        if proof:
            with open(proof_path, "w") as fh:
                for line in proof:
                    fh.write(str(line).rstrip() + "\n")
            proof_written = True
print(json.dumps({
    "solver": solver_name,
    "status": status,
    "stats": stats,
    "with_proof": with_proof,
    "proof_len": proof_len,
    "proof_written": proof_written,
}))
"""
        result = subprocess.run(
            [
                sys.executable,
                "-c",
                worker,
                chosen,
                str(cnf_path),
                str(proof_path),
                "1" if with_proof else "0",
            ],
            capture_output=True,
            text=True,
            timeout=time_limit_s + min(60, max(5, int(time_limit_s * 0.05))),
            check=False,
        )
        exit_code = result.returncode
        stdout = result.stdout or ""
        stderr = result.stderr or ""
        stdout_lines.extend(stdout.splitlines())
        if result.returncode == 0 and stdout.strip():
            payload = json.loads(stdout.splitlines()[-1])
            status = payload.get("status", "UNKNOWN")
            stats = payload.get("stats", {})
    except subprocess.TimeoutExpired as exc:
        status = "UNKNOWN"
        exit_code = -1
        stdout = exc.stdout or ""
        if isinstance(stdout, bytes):
            stdout = stdout.decode("utf-8", errors="replace")
        stderr = exc.stderr or ""
        if isinstance(stderr, bytes):
            stderr = stderr.decode("utf-8", errors="replace")
        stdout_lines.extend(str(stdout).splitlines())
    except Exception as exc:
        status = "UNKNOWN"
        exit_code = 2
        stderr = repr(exc)

    elapsed = time.time() - t0
    if stats:
        stdout_lines.append("stats: " + json.dumps(stats, sort_keys=True))

    return {
        "status": status,
        "solver_seconds": elapsed,
        "exit_code": exit_code,
        "stdout_tail": "\n".join(stdout_lines[-30:]),
        "stderr_tail": stderr,
        "pysat_stats": stats,
        "pysat_with_proof": with_proof,
    }


# ---------------------------------------------------------------------------
# Driver
# ---------------------------------------------------------------------------


def attack_one_chunk(
    chunk: dict[str, Any],
    N: int,
    K: int,
    triples: list[tuple[int, int, int]],
    window_constraints: list[tuple[list[int], int]],
    solver_binary: str,
    time_limit_s: int,
    out_dir: Path,
    keep_cnf: bool,
    extra_solver_args: list[str],
    pysat_with_proof: bool,
) -> dict[str, Any]:
    chunk_id = chunk["chunk_id"]
    fixed_in = chunk.get("fixed_in", [])
    fixed_out = chunk.get("fixed_out", [])

    t_encode_0 = time.time()
    cnf, stats = encode_chunk_as_cnf(
        N=N,
        K=K,
        fixed_in=fixed_in,
        fixed_out=fixed_out,
        triples=triples,
        window_constraints=window_constraints,
        force_endpoints=True,
    )
    encode_seconds = time.time() - t_encode_0

    cnf_path = out_dir / f"chunk_{chunk_id:08d}.cnf"
    proof_path = out_dir / f"chunk_{chunk_id:08d}.drat"
    cnf.to_file(str(cnf_path))

    solver_result = run_solver(
        cnf=cnf,
        cnf_path=cnf_path,
        proof_path=proof_path,
        solver_binary=solver_binary,
        time_limit_s=time_limit_s,
        extra_args=extra_solver_args,
        pysat_with_proof=pysat_with_proof,
    )

    if not keep_cnf:
        try:
            cnf_path.unlink()
        except OSError:
            pass

    record = {
        "chunk_id": chunk_id,
        "N": N,
        "K": K,
        "status": solver_result["status"],
        "encode_seconds": encode_seconds,
        "solver_seconds": solver_result["solver_seconds"],
        "seconds": encode_seconds + solver_result["solver_seconds"],
        "proof_path": (
            str(proof_path)
            if solver_result["status"] == "UNSAT"
            and proof_path.exists()
            and proof_path.stat().st_size > 0
            else None
        ),
        "proof_available": (
            solver_result["status"] == "UNSAT"
            and proof_path.exists()
            and proof_path.stat().st_size > 0
        ),
        "exit_code": solver_result["exit_code"],
        "stdout_tail": solver_result["stdout_tail"],
        "stderr_tail": solver_result["stderr_tail"],
        "solver_binary": solver_binary,
        "time_limit_s": time_limit_s,
        "pysat_with_proof": pysat_with_proof,
        **stats,
        "fixed_in_count": len(fixed_in),
        "fixed_out_count": len(fixed_out),
    }
    if "pysat_stats" in solver_result:
        record["pysat_stats"] = solver_result["pysat_stats"]
    return record


def main() -> int:
    ap = argparse.ArgumentParser(
        description="CDCL/SAT attack on T1b r_3(212) residual chunks."
    )
    ap.add_argument("--input", type=Path, required=True, help="Chunk JSONL.")
    ap.add_argument(
        "--output", type=Path, required=True, help="Output JSONL (one row per chunk)."
    )
    ap.add_argument("--N", type=int, default=212)
    ap.add_argument("--K", type=int, default=44)
    ap.add_argument(
        "--window-bounds",
        type=Path,
        default=Path("results/b003002.txt"),
        help="OEIS A003002 b-file.",
    )
    ap.add_argument(
        "--array-index",
        type=int,
        default=None,
        help="If set, only process the chunk at this 0-based row of the input.",
    )
    ap.add_argument(
        "--chunk-id",
        type=int,
        default=None,
        help="If set, only process the row matching this chunk_id.",
    )
    ap.add_argument(
        "--time-limit", type=int, default=14400, help="Per-chunk solver wall, seconds."
    )
    ap.add_argument(
        "--solver-binary",
        type=str,
        default="kissat",
        help="CDCL solver binary on PATH or absolute path.",
    )
    ap.add_argument(
        "--solver-arg",
        action="append",
        default=[],
        help="Extra arg to pass to the solver; repeat for multiple.",
    )
    ap.add_argument(
        "--pysat-with-proof",
        action="store_true",
        help=(
            "Request proof logging for PySAT backends. With --solver-binary "
            "pysat:auto this prefers Glucose over CaDiCaL because the Unity "
            "python-sat wheel emits non-empty proofs for Glucose."
        ),
    )
    ap.add_argument(
        "--work-dir",
        type=Path,
        default=None,
        help="Directory for CNF and DRAT scratch files. Default: tempdir.",
    )
    ap.add_argument(
        "--keep-cnf",
        action="store_true",
        help="Keep the CNF files after solving (default: delete to save disk).",
    )
    ap.add_argument(
        "--window-lengths",
        type=str,
        default=None,
        help=(
            "Comma-separated list of window lengths L to include. "
            "Default: all L with r_3(L) < min(L, K). Use a subset to keep the "
            "encoding small for low-RAM smoke tests. Use 'none' for a pure "
            "3-AP/cardinality encoding with no window constraints."
        ),
    )
    args = ap.parse_args()

    # Build the per-call invariants (3-AP triples, window constraints) once.
    triples = enumerate_3ap_triples(args.N)
    r3 = load_window_bounds(args.window_bounds)
    length_filter: set[int] | None = None
    if args.window_lengths is not None:
        raw_lengths = args.window_lengths.strip().lower()
        if raw_lengths in {"none", "off", "no", "empty"}:
            length_filter = set()
        else:
            length_filter = {int(x) for x in args.window_lengths.split(",") if x.strip()}
    window_constraints = build_window_constraints(
        args.N, args.K, r3, length_filter=length_filter
    )
    print(
        f"[setup] N={args.N} K={args.K} "
        f"triples={len(triples)} window_constraints={len(window_constraints)}",
        file=sys.stderr,
    )

    # Load and filter chunks
    rows = [json.loads(line) for line in args.input.read_text().splitlines() if line.strip()]
    if args.chunk_id is not None:
        rows = [r for r in rows if r.get("chunk_id") == args.chunk_id]
    if args.array_index is not None:
        if args.array_index < 0 or args.array_index >= len(rows):
            print(
                f"[error] array-index {args.array_index} out of range (have {len(rows)} rows)",
                file=sys.stderr,
            )
            return 2
        rows = [rows[args.array_index]]
    if not rows:
        print("[error] no rows to process", file=sys.stderr)
        return 2

    # Set up scratch directory
    if args.work_dir is None:
        work_dir = Path(tempfile.mkdtemp(prefix="r3_sat_attack_"))
    else:
        args.work_dir.mkdir(parents=True, exist_ok=True)
        work_dir = args.work_dir
    print(f"[setup] work_dir={work_dir}", file=sys.stderr)

    # Process each chunk; append a JSONL row after each.
    args.output.parent.mkdir(parents=True, exist_ok=True)
    seen_ids: set[int] = set()
    if args.output.exists():
        for line in args.output.read_text().splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                seen_ids.add(json.loads(line).get("chunk_id"))
            except json.JSONDecodeError:
                continue
    print(f"[setup] {len(seen_ids)} chunks already in {args.output}", file=sys.stderr)

    feasible_found = False
    with args.output.open("a") as fh:
        for row in rows:
            cid = row["chunk_id"]
            if cid in seen_ids:
                print(f"[skip] chunk_id={cid} already in output", file=sys.stderr)
                continue
            t0 = time.time()
            print(f"[run] chunk_id={cid} starting", file=sys.stderr)
            record = attack_one_chunk(
                chunk=row,
                N=args.N,
                K=args.K,
                triples=triples,
                window_constraints=window_constraints,
                solver_binary=args.solver_binary,
                time_limit_s=args.time_limit,
                out_dir=work_dir,
                keep_cnf=args.keep_cnf,
                extra_solver_args=list(args.solver_arg),
                pysat_with_proof=args.pysat_with_proof,
            )
            elapsed = time.time() - t0
            fh.write(json.dumps(record) + "\n")
            fh.flush()
            print(
                f"[done] chunk_id={cid} status={record['status']} "
                f"solver_s={record['solver_seconds']:.1f} wall_s={elapsed:.1f}",
                file=sys.stderr,
            )
            if record["status"] == "SAT":
                feasible_found = True
                print(
                    f"[ALERT] FEASIBLE solution returned for chunk_id={cid}. "
                    f"Run r3_verify.py on the witness before doing anything else.",
                    file=sys.stderr,
                )
                # Don't break; record everything so the SBATCH can scancel cleanly.

    return 1 if feasible_found else 0


if __name__ == "__main__":
    sys.exit(main())
