"""
Local optimization for fixed-size shifted-template constructions.

Given a normalized Sidon template B, this searches nearby templates of the
same size by replacing one nonzero mark at a time.  The objective is the best
admissible blocker interval density:

    interval_length / |B|^3

where admissible means the interval [L,R] in W(B) has L <= 0 <= max(B) <= R.

The script supports:
  - exhaustive one-swap search in a bounded value range;
  - simulated annealing/random-swap search for escaping shallow local traps.

Usage:
  python3 erdos_156/local_optimize_template.py --B 0,20,35,38,39,44,46,95,111,132,142,175,267,289,301,341,410,489,594,617
  python3 erdos_156/local_optimize_template.py --steps 50000 --restarts 8 --x-max 1200
"""
from __future__ import annotations

import argparse
import json
import math
import os
import random
from typing import Any

import beam_template_search as beam


THIS_DIR = os.path.dirname(os.path.abspath(__file__))
RESULTS = os.path.join(THIS_DIR, "results")
DEFAULT_B = [
    0, 20, 35, 38, 39, 44, 46, 95, 111, 132,
    142, 175, 267, 289, 301, 341, 410, 489, 594, 617,
]


def parse_template(raw: str) -> list[int]:
    vals = sorted(int(part.strip()) for part in raw.split(",") if part.strip())
    if not vals:
        raise argparse.ArgumentTypeError("template must be nonempty")
    if vals[0] != 0:
        raise argparse.ArgumentTypeError("template must be normalized with min 0")
    if len(vals) != len(set(vals)):
        raise argparse.ArgumentTypeError("template entries must be distinct")
    return vals


def metric(B: list[int]) -> dict[str, Any] | None:
    row = beam.template_metric(B)
    if row is None:
        return None
    return {
        "B": row["B"],
        "k": row["k"],
        "max_B": row["max_B"],
        "interval": row["interval"],
        "interval_length": row["interval_length"],
        "covered_N": row["covered_N"],
        "interval_length_over_k3": row["interval_length_over_k3"],
        "covered_end_over_k3": row["covered_end_over_k3"],
        "W_size": row["W_size"],
    }


def score(row: dict[str, Any] | None) -> tuple[float, float, int, int]:
    if row is None:
        return (-1.0, -1.0, -1, 0)
    return (
        row["interval_length_over_k3"],
        row["covered_end_over_k3"],
        row["interval_length"],
        -row["max_B"],
    )


def replace_mark(B: list[int], index: int, value: int) -> list[int] | None:
    if index == 0 or value <= 0:
        return None
    if value in B and value != B[index]:
        return None
    C = list(B)
    C[index] = value
    C = sorted(C)
    if C[0] != 0 or len(C) != len(set(C)):
        return None
    if not beam.is_sidon(C):
        return None
    return C


def exhaustive_one_swap(B: list[int], x_min: int, x_max: int) -> dict[str, Any]:
    start = metric(B)
    best = start
    best_move = None
    checked = 0
    feasible = 0
    for index in range(1, len(B)):
        old = B[index]
        for value in range(x_min, x_max + 1):
            if value == old:
                continue
            checked += 1
            C = replace_mark(B, index, value)
            if C is None:
                continue
            feasible += 1
            row = metric(C)
            if score(row) > score(best):
                best = row
                best_move = {"index": index, "old": old, "new": value}
    return {
        "checked_replacements": checked,
        "feasible_replacements": feasible,
        "start": start,
        "best": best,
        "best_move": best_move,
        "improved": score(best) > score(start),
    }


def anneal_once(
    B: list[int],
    steps: int,
    x_min: int,
    x_max: int,
    start_temp: float,
    end_temp: float,
    rng: random.Random,
) -> dict[str, Any]:
    current_B = list(B)
    current = metric(current_B)
    best = current
    best_step = 0
    accepted = 0
    feasible = 0
    history = []

    for step in range(1, steps + 1):
        index = rng.randrange(1, len(current_B))
        value = rng.randint(x_min, x_max)
        C = replace_mark(current_B, index, value)
        if C is None:
            continue
        feasible += 1
        row = metric(C)
        if row is None:
            continue
        current_score = score(current)
        row_score = score(row)
        delta = row_score[0] - current_score[0]
        if steps <= 1:
            temp = end_temp
        else:
            frac = (step - 1) / (steps - 1)
            temp = start_temp * ((end_temp / start_temp) ** frac)
        accept = row_score >= current_score
        if not accept and temp > 0:
            accept = rng.random() < math.exp(delta / temp)
        if accept:
            current_B = C
            current = row
            accepted += 1
        if score(row) > score(best):
            best = row
            best_step = step
            history.append({
                "step": step,
                "score": row["interval_length_over_k3"],
                "covered_N": row["covered_N"],
                "interval": row["interval"],
                "max_B": row["max_B"],
                "B": row["B"],
            })

    return {
        "best": best,
        "best_step": best_step,
        "accepted": accepted,
        "feasible_moves": feasible,
        "history": history,
    }


def anneal(
    B: list[int],
    restarts: int,
    steps: int,
    x_min: int,
    x_max: int,
    start_temp: float,
    end_temp: float,
    seed: int,
) -> dict[str, Any]:
    rng = random.Random(seed)
    runs = []
    best = metric(B)
    for restart in range(restarts):
        run_seed = rng.randrange(1 << 60)
        run_rng = random.Random(run_seed)
        run = anneal_once(B, steps, x_min, x_max, start_temp, end_temp, run_rng)
        run["restart"] = restart
        run["seed"] = run_seed
        runs.append(run)
        if score(run["best"]) > score(best):
            best = run["best"]
    return {
        "start": metric(B),
        "best": best,
        "runs": runs,
        "improved": score(best) > score(metric(B)),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--B", type=parse_template, default=DEFAULT_B)
    parser.add_argument("--x-min", type=int, default=1)
    parser.add_argument("--x-max", type=int, default=1200)
    parser.add_argument("--skip-exhaustive", action="store_true")
    parser.add_argument("--steps", type=int, default=40_000)
    parser.add_argument("--restarts", type=int, default=8)
    parser.add_argument("--start-temp", type=float, default=0.01)
    parser.add_argument("--end-temp", type=float, default=0.00005)
    parser.add_argument("--seed", type=int, default=156)
    parser.add_argument("--output", default=os.path.join(RESULTS, "template_local_opt_156.json"))
    args = parser.parse_args()

    if args.x_min < 1 or args.x_max < args.x_min:
        parser.error("invalid x range")
    if args.steps < 1 or args.restarts < 1:
        parser.error("--steps and --restarts must be positive")

    start = metric(args.B)
    if start is None:
        raise ValueError("initial template has no admissible interval")

    exhaustive = None
    if not args.skip_exhaustive:
        exhaustive = exhaustive_one_swap(args.B, args.x_min, args.x_max)
        anneal_start = exhaustive["best"]["B"]
    else:
        anneal_start = args.B

    annealed = anneal(
        anneal_start,
        args.restarts,
        args.steps,
        args.x_min,
        args.x_max,
        args.start_temp,
        args.end_temp,
        args.seed,
    )

    best = start
    for candidate in [exhaustive["best"] if exhaustive else None, annealed["best"]]:
        if score(candidate) > score(best):
            best = candidate

    output = {
        "args": vars(args),
        "start": start,
        "exhaustive_one_swap": exhaustive,
        "anneal": annealed,
        "best": best,
        "improved": score(best) > score(start),
    }
    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as fh:
        json.dump(output, fh, indent=2)

    print("Start:", {
        "score": start["interval_length_over_k3"],
        "covered_N": start["covered_N"],
        "interval": start["interval"],
        "max_B": start["max_B"],
    })
    if exhaustive is not None:
        print("One-swap:", {
            "improved": exhaustive["improved"],
            "checked": exhaustive["checked_replacements"],
            "feasible": exhaustive["feasible_replacements"],
            "best_move": exhaustive["best_move"],
            "best_score": exhaustive["best"]["interval_length_over_k3"],
            "best_N": exhaustive["best"]["covered_N"],
        })
    print("Anneal:", {
        "improved": annealed["improved"],
        "best_score": annealed["best"]["interval_length_over_k3"],
        "best_N": annealed["best"]["covered_N"],
    })
    print("Best:", {
        "improved": output["improved"],
        "score": best["interval_length_over_k3"],
        "covered_N": best["covered_N"],
        "interval": best["interval"],
        "max_B": best["max_B"],
        "B": best["B"],
    })
    print(f"Wrote {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
