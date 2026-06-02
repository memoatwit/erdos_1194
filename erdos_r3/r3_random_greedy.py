"""
Randomized lower-bound search for large 3-AP-free subsets.

This is intentionally a witness finder, not an upper-bound prover.  It searches
for a fixed-size subset A of [1..N] with zero 3-term arithmetic progressions by
running randomized repair on a K-subset and minimizing the number of violated
3-AP constraints.

Usage:
  python3 erdos_r3/r3_random_greedy.py --N-start 211 --N-end 212 --target 43 \
    --restarts 50000 --output erdos_r3/results/N212_K43_witness.json
"""
from __future__ import annotations

import argparse
import json
import math
import random
import time
from pathlib import Path

from r3_cpsat import arithmetic_progressions
from r3_verify import verify


def build_incidence(N: int) -> tuple[list[tuple[int, int, int]], list[list[int]]]:
    triples = arithmetic_progressions(N)
    incidence = [[] for _ in range(N + 1)]
    for idx, triple in enumerate(triples):
        for value in triple:
            incidence[value].append(idx)
    return triples, incidence


def random_k_set(N: int, K: int, rng: random.Random) -> set[int]:
    return set(rng.sample(range(1, N + 1), K))


def counts_for_set(triples: list[tuple[int, int, int]], selected: set[int]) -> list[int]:
    return [sum(1 for value in triple if value in selected) for triple in triples]


def violated_indices(counts: list[int]) -> set[int]:
    return {idx for idx, count in enumerate(counts) if count == 3}


def swap_delta(
    triples: list[tuple[int, int, int]],
    incidence: list[list[int]],
    counts: list[int],
    remove_value: int,
    add_value: int,
) -> int:
    touched = set(incidence[remove_value])
    touched.update(incidence[add_value])
    delta = 0
    for idx in touched:
        before = counts[idx]
        triple = triples[idx]
        after = before
        if remove_value in triple:
            after -= 1
        if add_value in triple:
            after += 1
        delta += int(after == 3) - int(before == 3)
    return delta


def apply_swap(
    triples: list[tuple[int, int, int]],
    incidence: list[list[int]],
    counts: list[int],
    selected: set[int],
    violations: set[int],
    remove_value: int,
    add_value: int,
) -> None:
    selected.remove(remove_value)
    selected.add(add_value)
    touched = set(incidence[remove_value])
    touched.update(incidence[add_value])
    for idx in touched:
        triple = triples[idx]
        counts[idx] = sum(1 for value in triple if value in selected)
        if counts[idx] == 3:
            violations.add(idx)
        else:
            violations.discard(idx)


def repair_search(
    N: int,
    K: int,
    *,
    restarts: int,
    steps_per_restart: int,
    add_samples: int,
    seed: int,
    deadline: float | None = None,
) -> dict:
    rng = random.Random(seed)
    triples, incidence = build_incidence(N)
    best: dict = {
        "N": N,
        "target": K,
        "found": False,
        "best_violation_count": len(triples),
        "best_set": [],
        "restarts_completed": 0,
        "steps_completed": 0,
    }

    all_values = set(range(1, N + 1))
    for restart in range(1, restarts + 1):
        if deadline is not None and time.time() >= deadline:
            break
        selected = random_k_set(N, K, rng)
        counts = counts_for_set(triples, selected)
        violations = violated_indices(counts)
        temperature = max(0.25, len(violations) / 4)

        if len(violations) < best["best_violation_count"]:
            best["best_violation_count"] = len(violations)
            best["best_set"] = sorted(selected)

        for step in range(steps_per_restart):
            best["steps_completed"] += 1
            if not violations:
                witness = sorted(selected)
                report = verify(witness, N=N)
                return {
                    **best,
                    "found": True,
                    "best_violation_count": 0,
                    "best_set": witness,
                    "witness": witness,
                    "witness_report": report,
                    "restarts_completed": restart,
                }
            if deadline is not None and time.time() >= deadline:
                break

            bad_triple = triples[rng.choice(tuple(violations))]
            remove_candidates = list(bad_triple)
            rng.shuffle(remove_candidates)
            unselected = list(all_values - selected)
            sampled_adds = rng.sample(unselected, min(add_samples, len(unselected)))

            best_move: tuple[int, int, int] | None = None
            for remove_value in remove_candidates:
                for add_value in sampled_adds:
                    delta = swap_delta(triples, incidence, counts, remove_value, add_value)
                    if best_move is None or delta < best_move[0]:
                        best_move = (delta, remove_value, add_value)
                        if delta < 0:
                            break
                if best_move and best_move[0] < 0:
                    break

            if best_move is None:
                break
            delta, remove_value, add_value = best_move
            accept = delta <= 0 or rng.random() < math.exp(-delta / max(temperature, 0.05))
            if accept:
                apply_swap(triples, incidence, counts, selected, violations, remove_value, add_value)
                if len(violations) < best["best_violation_count"]:
                    best["best_violation_count"] = len(violations)
                    best["best_set"] = sorted(selected)
            temperature *= 0.9995

        best["restarts_completed"] = restart
    best["witness"] = best["best_set"]
    best["witness_report"] = verify(best["best_set"], N=N) if best["best_set"] else None
    return best


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--N-start", type=int, required=True)
    parser.add_argument("--N-end", type=int, required=True)
    parser.add_argument("--target", type=int, required=True)
    parser.add_argument("--restarts", type=int, default=10000)
    parser.add_argument("--steps-per-restart", type=int, default=2500)
    parser.add_argument("--add-samples", type=int, default=48)
    parser.add_argument("--seed", type=int, default=1194)
    parser.add_argument("--time-limit", type=float, default=None)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    t0 = time.time()
    deadline = t0 + args.time_limit if args.time_limit is not None else None
    args.output.parent.mkdir(parents=True, exist_ok=True)

    attempts = []
    found_payload = None
    for N in range(args.N_start, args.N_end + 1):
        result = repair_search(
            N,
            args.target,
            restarts=args.restarts,
            steps_per_restart=args.steps_per_restart,
            add_samples=args.add_samples,
            seed=args.seed + N,
            deadline=deadline,
        )
        attempts.append(result)
        if result["found"]:
            found_payload = {
                "N": args.N_end,
                "found_at_N": N,
                "target": args.target,
                "A": result["witness"],
                "size": len(result["witness"]),
                "seconds": round(time.time() - t0, 4),
                "attempts": attempts,
            }
            break
        if deadline is not None and time.time() >= deadline:
            break

    payload = found_payload or {
        "N": args.N_end,
        "target": args.target,
        "found": False,
        "seconds": round(time.time() - t0, 4),
        "attempts": attempts,
    }
    with args.output.open("w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2)
        fh.write("\n")
    print(json.dumps({
        "output": str(args.output),
        "found": bool(found_payload),
        "N": payload["N"],
        "target": args.target,
        "size": payload.get("size"),
        "seconds": payload["seconds"],
    }, indent=2), flush=True)
    return 0 if found_payload else 1


if __name__ == "__main__":
    raise SystemExit(main())
