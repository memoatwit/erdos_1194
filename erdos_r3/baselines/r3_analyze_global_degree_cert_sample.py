#!/usr/bin/env python3
"""Validate and summarize the global-degree certificate-transfer sample."""

from __future__ import annotations

import argparse
import glob
import json
import statistics
from pathlib import Path
from typing import Any


def numeric_summary(values: list[float]) -> dict[str, float]:
    return {
        "min": min(values),
        "median": statistics.median(values),
        "max": max(values),
        "sum": sum(values),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--selection",
        default="results/global_degree_cert_sample6.jsonl",
    )
    parser.add_argument(
        "--provenance-glob",
        default="results/global_degree_cert_sample6_provenance/chunk_*.json",
    )
    parser.add_argument(
        "--output",
        default="results/global_degree_cert_sample6_verification_summary.json",
    )
    args = parser.parse_args()

    selected = [
        json.loads(line)
        for line in Path(args.selection).read_text().splitlines()
        if line.strip()
    ]
    provenance: list[dict[str, Any]] = [
        json.loads(Path(name).read_text())
        for name in sorted(glob.glob(args.provenance_glob))
    ]
    if len(selected) != 6 or len(provenance) != 6:
        raise ValueError(
            f"expected six selection and provenance rows, found {len(selected)} and {len(provenance)}"
        )

    selected_by_chunk = {int(row["chunk_id"]): row for row in selected}
    provenance_by_chunk = {int(row["chunk_id"]): row for row in provenance}
    if len(selected_by_chunk) != 6 or set(selected_by_chunk) != set(provenance_by_chunk):
        raise ValueError("selection/provenance chunk IDs do not match one-to-one")

    rows = []
    for chunk_id in sorted(selected_by_chunk):
        selection = selected_by_chunk[chunk_id]
        proof = provenance_by_chunk[chunk_id]
        if proof["status"] != "UNSAT":
            raise ValueError(f"chunk {chunk_id} did not return UNSAT")
        if not proof["cnf_hash_matches_survey"]:
            raise ValueError(f"chunk {chunk_id} CNF hash does not match survey")
        if proof["cnf_sha256"] != selection["prior_cnf_sha256"]:
            raise ValueError(f"chunk {chunk_id} selection/proof CNF hashes differ")
        if proof["drat_trim_status"] != "VERIFIED":
            raise ValueError(f"chunk {chunk_id} DRAT verification failed")
        if proof["cake_lpr_status"] != "VERIFIED":
            raise ValueError(f"chunk {chunk_id} cake_lpr verification failed")
        if float(proof["selection_quantile"]) != float(selection["selection_quantile"]):
            raise ValueError(f"chunk {chunk_id} selection quantile changed")
        rows.append(
            {
                "chunk_id": chunk_id,
                "selection_quantile": proof["selection_quantile"],
                "prior_solver_seconds": proof["prior_solver_seconds"],
                "proof_solver_seconds": proof["proof_solver_seconds"],
                "drat_trim_seconds": proof["drat_trim_seconds"],
                "cake_lpr_seconds": proof["cake_lpr_seconds"],
                "cnf_sha256": proof["cnf_sha256"],
                "drat_sha256": proof["drat_sha256"],
                "lrat_sha256": proof["lrat_sha256"],
                "cnf_bytes": proof["cnf_bytes"],
                "drat_bytes": proof["drat_bytes"],
                "lrat_bytes": proof["lrat_bytes"],
            }
        )

    output = {
        "selected_cases": len(rows),
        "all_unsat": True,
        "all_cnf_hashes_match_survey": True,
        "all_drat_trim_verified": True,
        "all_cake_lpr_verified": True,
        "selection_quantiles": sorted(row["selection_quantile"] for row in rows),
        "prior_solver_seconds": numeric_summary(
            [float(row["prior_solver_seconds"]) for row in rows]
        ),
        "proof_solver_seconds": numeric_summary(
            [float(row["proof_solver_seconds"]) for row in rows]
        ),
        "drat_trim_seconds": numeric_summary(
            [float(row["drat_trim_seconds"]) for row in rows]
        ),
        "cake_lpr_seconds": numeric_summary(
            [float(row["cake_lpr_seconds"]) for row in rows]
        ),
        "artifact_bytes": {
            "cnf_sum": sum(int(row["cnf_bytes"]) for row in rows),
            "drat_sum": sum(int(row["drat_bytes"]) for row in rows),
            "lrat_sum": sum(int(row["lrat_bytes"]) for row in rows),
        },
        "rows": rows,
    }
    Path(args.output).write_text(json.dumps(output, indent=2, sort_keys=True) + "\n")
    print(json.dumps(output, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
