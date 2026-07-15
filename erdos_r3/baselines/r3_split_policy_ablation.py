#!/usr/bin/env python3
"""Matched raw-assignment ablation for depth-24 split-variable policies.

Each sampled 24-bit assignment is applied to five split-variable policies.
All five arms run sequentially inside one SLURM task, which keeps hardware and
the sampled bit pattern matched while rotating solver order across tasks.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import random
import sys
from pathlib import Path

R3_DIR = Path(__file__).resolve().parents[1]
if str(R3_DIR) not in sys.path:
    sys.path.insert(0, str(R3_DIR))

from r3_cpsat import (  # noqa: E402
    arithmetic_progressions,
    load_int_set,
    load_window_bounds,
    solve_r3_cpsat,
)
from r3_verify import verify  # noqa: E402


POLICY_NAMES = (
    "deployed_witness_numeric",
    "witness_degree",
    "witness_random",
    "global_degree",
    "global_random",
)


def stable_hash(value: object) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def load_ordered_int_list(path: Path) -> list[int]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, list):
        raise ValueError(f"{path} must contain a JSON list")
    values = [int(value) for value in raw]
    if len(values) != len(set(values)):
        raise ValueError(f"{path} contains duplicate values")
    return values


def degree_order(N: int, excluded: set[int]) -> list[int]:
    degrees = {value: 0 for value in range(1, N + 1)}
    for triple in arithmetic_progressions(N):
        for value in triple:
            degrees[value] += 1
    center = (N + 1) / 2
    return sorted(
        (value for value in range(1, N + 1) if value not in excluded),
        key=lambda value: (-degrees[value], abs(value - center), value),
    )


def build_policies(
    *,
    N: int,
    split_count: int,
    witness: list[int],
    witness_degree_order: list[int],
    fixed_endpoints: list[int],
    policy_seed: int,
) -> dict[str, list[int]]:
    excluded = set(fixed_endpoints)
    witness_pool = [value for value in witness if value not in excluded]
    if len(witness_pool) < split_count:
        raise ValueError("witness does not contain enough unfixed split variables")

    witness_ranked = [value for value in witness_degree_order if value in witness_pool]
    if len(witness_ranked) < split_count:
        raise ValueError("witness degree-order file does not contain enough variables")

    global_pool = [value for value in range(1, N + 1) if value not in excluded]
    witness_rng = random.Random(policy_seed)
    global_rng = random.Random(policy_seed + 1)
    return {
        # This is the policy actually deployed in the campaign.  The generic
        # set loader sorted the stored degree-order JSON before truncation.
        "deployed_witness_numeric": sorted(witness_pool)[:split_count],
        "witness_degree": witness_ranked[:split_count],
        "witness_random": witness_rng.sample(witness_pool, split_count),
        "global_degree": degree_order(N, excluded)[:split_count],
        "global_random": global_rng.sample(global_pool, split_count),
    }


def sampled_raw_ids(*, split_count: int, sample_size: int, sample_seed: int) -> list[int]:
    population_size = 1 << split_count
    if sample_size > population_size:
        raise ValueError("sample size exceeds the raw assignment space")
    return sorted(random.Random(sample_seed).sample(range(population_size), sample_size))


def decode_assignment(raw_id: int, variables: list[int]) -> tuple[list[int], list[int]]:
    fixed_in = []
    fixed_out = []
    for bit_index, value in enumerate(variables):
        (fixed_in if (raw_id >> bit_index) & 1 else fixed_out).append(value)
    return sorted(fixed_in), sorted(fixed_out)


def run_policy(
    *,
    policy: str,
    variables: list[int],
    raw_id: int,
    sample_index: int,
    order_position: int,
    N: int,
    K: int,
    fixed_endpoints: list[int],
    hint: list[int],
    window_bounds: dict[int, int],
    time_limit: float,
    workers: int,
) -> dict:
    assignment_in, assignment_out = decode_assignment(raw_id, variables)
    fixed_in = sorted(set(fixed_endpoints) | set(assignment_in))
    fixed_out = sorted(set(assignment_out))
    prefix_report = verify(fixed_in, N=N)
    base = {
        "sample_index": sample_index,
        "raw_assignment_id": raw_id,
        "policy": policy,
        "order_position": order_position,
        "split_count": len(variables),
        "split_variables": variables,
        "split_variables_sha256": stable_hash(variables),
        "assignment_fixed_in": assignment_in,
        "assignment_fixed_out": assignment_out,
        "fixed_in": fixed_in,
        "fixed_out": fixed_out,
        "workers": workers,
        "time_limit": time_limit,
    }
    if not prefix_report.get("ok"):
        return {
            **base,
            "status": "PRUNED_PREFIX_AP",
            "solver_status_name": None,
            "seconds": 0.0,
            "branches": 0,
            "conflicts": 0,
            "certifies": True,
            "witness": [],
            "witness_verified": False,
        }

    result = solve_r3_cpsat(
        N,
        decision_size=K,
        time_limit=time_limit,
        workers=workers,
        symmetry_break=True,
        fixed_in=fixed_in,
        fixed_out=fixed_out,
        hint=hint,
        branch_order="degree",
        branch_value="min",
        fixed_search=True,
        window_bounds=window_bounds,
    )
    if result["is_feasible_for_decision_size"]:
        status = "FEASIBLE"
    elif result["solver_status_name"] == "INFEASIBLE":
        status = "INFEASIBLE"
    else:
        status = "UNKNOWN"
    return {
        **base,
        "status": status,
        "solver_status_name": result["solver_status_name"],
        "seconds": result["seconds"],
        "wall_time": result["wall_time"],
        "branches": result["branches"],
        "conflicts": result["conflicts"],
        "window_constraints": result["window_constraints"],
        "certifies": result["certifies_optimal"],
        "witness": result["witness"] if status == "FEASIBLE" else [],
        "witness_verified": result["witness_verified"],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sample-index", type=int, required=True)
    parser.add_argument("--sample-size", type=int, default=500)
    parser.add_argument("--sample-seed", type=int, default=20260715)
    parser.add_argument("--policy-seed", type=int, default=1194)
    parser.add_argument("--split-count", type=int, default=24)
    parser.add_argument("--N", type=int, default=212)
    parser.add_argument("--K", type=int, default=44)
    parser.add_argument("--time-limit", type=float, default=60.0)
    parser.add_argument("--workers", type=int, default=8)
    parser.add_argument(
        "--witness",
        type=Path,
        default=R3_DIR / "results/N212_K43_witness.json",
    )
    parser.add_argument(
        "--witness-degree-order",
        type=Path,
        default=R3_DIR / "results/N212_K43_witness_degree_order.json",
    )
    parser.add_argument(
        "--fixed-endpoints",
        type=Path,
        default=R3_DIR / "results/N212_K44_force_endpoints.json",
    )
    parser.add_argument(
        "--window-bounds",
        type=Path,
        default=R3_DIR / "results/b003002.txt",
    )
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    if args.sample_index < 0 or args.sample_index >= args.sample_size:
        parser.error("--sample-index must be in [0, sample-size)")

    witness = load_int_set(args.witness)
    witness_degree_order = load_ordered_int_list(args.witness_degree_order)
    fixed_endpoints = load_int_set(args.fixed_endpoints)
    window_bounds = load_window_bounds(args.window_bounds)
    policies = build_policies(
        N=args.N,
        split_count=args.split_count,
        witness=witness,
        witness_degree_order=witness_degree_order,
        fixed_endpoints=fixed_endpoints,
        policy_seed=args.policy_seed,
    )
    raw_ids = sampled_raw_ids(
        split_count=args.split_count,
        sample_size=args.sample_size,
        sample_seed=args.sample_seed,
    )
    raw_id = raw_ids[args.sample_index]
    rotation = args.sample_index % len(POLICY_NAMES)
    policy_order = list(POLICY_NAMES[rotation:] + POLICY_NAMES[:rotation])

    args.output.parent.mkdir(parents=True, exist_ok=True)
    rows = []
    for order_position, policy in enumerate(policy_order):
        row = run_policy(
            policy=policy,
            variables=policies[policy],
            raw_id=raw_id,
            sample_index=args.sample_index,
            order_position=order_position,
            N=args.N,
            K=args.K,
            fixed_endpoints=fixed_endpoints,
            hint=witness,
            window_bounds=window_bounds,
            time_limit=args.time_limit,
            workers=args.workers,
        )
        row.update({
            "sample_size": args.sample_size,
            "sample_seed": args.sample_seed,
            "sample_sha256": stable_hash(raw_ids),
            "policy_seed": args.policy_seed,
            "policy_order": policy_order,
        })
        rows.append(row)
        if row["status"] == "FEASIBLE":
            break

    tmp = args.output.with_name(args.output.name + ".tmp")
    with tmp.open("w", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row, sort_keys=True) + "\n")
    tmp.replace(args.output)
    print(json.dumps({
        "sample_index": args.sample_index,
        "raw_assignment_id": raw_id,
        "statuses": {row["policy"]: row["status"] for row in rows},
    }, sort_keys=True))
    return 2 if any(row["status"] == "FEASIBLE" for row in rows) else 0


if __name__ == "__main__":
    raise SystemExit(main())
