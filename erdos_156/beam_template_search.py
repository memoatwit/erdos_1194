"""
Beam search for shifted-template maximal Sidon constructions.

This is the non-greedy counterpart to extend_template_chain.py.  It keeps many
candidate templates at each size and scores them by the density of the best
admissible consecutive interval in W(B):

    score = interval_length / |B|^3.

An admissible interval [L,R] must satisfy L <= 0 and R >= max(B), because then
it certifies shifted maximal Sidon witnesses for

    max(B)+1 <= N <= R+1-L.

By default the search requires each extension to overlap the previous
template's covered N-range.  This keeps the chain relevant to covering every
N in a long range.  Use --no-require-overlap to search more freely for dense
templates.

Usage:
  python3 erdos_156/beam_template_search.py --k-max 16 --beam-width 64
  python3 erdos_156/beam_template_search.py --k-max 14 --beam-width 128 --no-require-overlap --x-factor 0.6
"""
from __future__ import annotations

import argparse
import json
import os
from itertools import combinations
from typing import Iterable


THIS_DIR = os.path.dirname(os.path.abspath(__file__))
RESULTS = os.path.join(THIS_DIR, "results")
DEFAULT_B = [0, 40, 60, 61, 63, 67, 96, 112]


def parse_template(raw: str) -> list[int]:
    vals = sorted(int(part.strip()) for part in raw.split(",") if part.strip())
    if len(vals) != len(set(vals)):
        raise argparse.ArgumentTypeError("template entries must be distinct")
    if not vals:
        raise argparse.ArgumentTypeError("template must be nonempty")
    if min(vals) != 0:
        raise argparse.ArgumentTypeError("template must be normalized with min 0")
    return vals


def intervals(vals: Iterable[int]) -> list[list[int]]:
    xs = sorted(set(vals))
    if not xs:
        return []
    out = []
    start = prev = xs[0]
    for x in xs[1:]:
        if x == prev + 1:
            prev = x
        else:
            out.append([start, prev])
            start = prev = x
    out.append([start, prev])
    return out


def all_pair_diffs(B: list[int]) -> list[int]:
    return [b - a for a, b in combinations(sorted(B), 2)]


def is_sidon(B: list[int]) -> bool:
    diffs = all_pair_diffs(B)
    return len(diffs) == len(set(diffs))


def can_append(B: list[int], x: int, existing_diffs: set[int]) -> bool:
    if x <= max(B) or x in B:
        return False
    new_diffs = [x - b for b in B]
    return len(new_diffs) == len(set(new_diffs)) and not (existing_diffs & set(new_diffs))


def blocker_set(B: list[int]) -> set[int]:
    B = sorted(B)
    diffs = sorted(set(all_pair_diffs(B)))
    W = set(B)
    for b in B:
        for d in diffs:
            W.add(b - d)
            W.add(b + d)
    for a, b in combinations(B, 2):
        if (a + b) % 2 == 0:
            W.add((a + b) // 2)
    return W


def template_metric(B: list[int]) -> dict | None:
    B = sorted(B)
    k = len(B)
    M = max(B)
    W = blocker_set(B)
    admissible = []
    for L, R in intervals(W):
        if L <= 0 and R >= M:
            length = R - L + 1
            covered_start = M + 1
            covered_end = R + 1 - L
            admissible.append({
                "interval": [L, R],
                "interval_length": length,
                "covered_N": [covered_start, covered_end],
                "interval_length_over_k3": length / (k ** 3),
                "covered_end_over_k3": covered_end / (k ** 3),
            })
    if not admissible:
        return None
    best = max(
        admissible,
        key=lambda row: (
            row["interval_length_over_k3"],
            row["covered_end_over_k3"],
            row["interval_length"],
            row["covered_N"][1],
        ),
    )
    best.update({
        "B": B,
        "k": k,
        "max_B": M,
        "W_size": len(W),
        "admissible_interval_count": len(admissible),
    })
    return best


def candidate_upper_bound(state: dict, next_k: int, args: argparse.Namespace) -> int:
    M = state["max_B"]
    if args.require_overlap:
        return state["covered_N"][1]
    cubic_bound = int(args.x_factor * (next_k ** 3))
    window_bound = M + args.x_window
    return max(cubic_bound, window_bound)


def expand_state(state: dict, args: argparse.Namespace) -> list[dict]:
    B = state["B"]
    next_k = len(B) + 1
    x_hi = candidate_upper_bound(state, next_k, args)
    existing_diffs = set(all_pair_diffs(B))
    out = []
    for x in range(max(B) + 1, x_hi + 1):
        if not can_append(B, x, existing_diffs):
            continue
        C = sorted(B + [x])
        metric = template_metric(C)
        if metric is None:
            continue
        if args.require_overlap and metric["covered_N"][0] > state["covered_N"][1] + 1:
            continue
        metric["parent_B"] = B
        metric["appended"] = x
        out.append(metric)
    return out


def state_sort_key(row: dict) -> tuple:
    return (
        row["interval_length_over_k3"],
        row["covered_end_over_k3"],
        row["interval_length"],
        row["covered_N"][1],
        -row["max_B"],
    )


def run_beam(args: argparse.Namespace) -> dict:
    seed = sorted(args.B)
    if not is_sidon(seed):
        raise ValueError("seed template is not Sidon")
    seed_metric = template_metric(seed)
    if seed_metric is None:
        raise ValueError("seed template has no admissible interval")
    seed_metric["appended"] = None
    seed_metric["parent_B"] = None

    beam = [seed_metric]
    levels = [{
        "k": len(seed),
        "candidate_count": 1,
        "beam": beam,
    }]

    for next_k in range(len(seed) + 1, args.k_max + 1):
        seen: dict[tuple[int, ...], dict] = {}
        generated = 0
        for state in beam:
            children = expand_state(state, args)
            generated += len(children)
            for child in children:
                key = tuple(child["B"])
                current = seen.get(key)
                if current is None or state_sort_key(child) > state_sort_key(current):
                    seen[key] = child
        candidates = sorted(seen.values(), key=state_sort_key, reverse=True)
        beam = candidates[:args.beam_width]
        levels.append({
            "k": next_k,
            "generated_count": generated,
            "candidate_count": len(candidates),
            "beam": beam,
        })
        if not beam:
            break

    best_by_k = [level["beam"][0] for level in levels if level["beam"]]
    best_overall = max(best_by_k, key=state_sort_key)
    deepest_best = best_by_k[-1]
    deepest_best_path = reconstruct_path(levels, deepest_best)
    return {
        "seed_B": seed,
        "k_max_requested": args.k_max,
        "beam_width": args.beam_width,
        "x_factor": args.x_factor,
        "x_window": args.x_window,
        "require_overlap": args.require_overlap,
        "levels": levels,
        "best_by_k": best_by_k,
        "best_overall": best_overall,
        "deepest_best_path": deepest_best_path,
        "deepest_best_path_covered_union": compact_union(row["covered_N"] for row in deepest_best_path),
    }


def reconstruct_path(levels: list[dict], final_state: dict) -> list[dict]:
    """Follow parent_B links for a state that appears in the saved levels."""
    path = []
    target_B = final_state["B"]
    for level in reversed(levels):
        match = None
        for state in level["beam"]:
            if state["B"] == target_B:
                match = state
                break
        if match is None:
            break
        path.append(match)
        parent = match.get("parent_B")
        if parent is None:
            break
        target_B = parent
    return list(reversed(path))


def compact_union(ranges: Iterable[list[int]]) -> list[list[int]]:
    vals = set()
    for start, end in ranges:
        vals.update(range(start, end + 1))
    return intervals(vals)


def write_json(data: dict, path: str) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2)


def print_summary(data: dict, top: int) -> None:
    print("Best by size:")
    print("k  append maxB interval       covered_N len/k^3 end/k^3 generated candidates")
    print("-- ------ ---- -------------- -------- ------- ------- --------- ----------")
    for level, best in zip(data["levels"], data["best_by_k"]):
        x = "-" if best.get("appended") is None else str(best["appended"])
        L, R = best["interval"]
        a, b = best["covered_N"]
        print(
            f"{best['k']:2d} {x:>6} {best['max_B']:4d} "
            f"[{L:4d},{R:4d}] {a:4d}-{b:<4d} "
            f"{best['interval_length_over_k3']:.4f}  "
            f"{best['covered_end_over_k3']:.4f}  "
            f"{level.get('generated_count', 1):9d} {level.get('candidate_count', 1):10d}"
        )

    last = data["levels"][-1]
    if last["beam"]:
        print()
        print(f"Top {min(top, len(last['beam']))} at k={last['k']}:")
        for row in last["beam"][:top]:
            L, R = row["interval"]
            a, b = row["covered_N"]
            print(
                f"  score={row['interval_length_over_k3']:.4f} "
                f"end/k^3={row['covered_end_over_k3']:.4f} "
                f"append={row.get('appended')} maxB={row['max_B']} "
                f"interval=[{L},{R}] N={a}-{b} B={row['B']}"
            )
    if data.get("deepest_best_path"):
        print()
        print("Deepest-best path covered union:", data["deepest_best_path_covered_union"])


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--B", type=parse_template, default=DEFAULT_B)
    parser.add_argument("--k-max", type=int, default=16)
    parser.add_argument("--beam-width", type=int, default=64)
    parser.add_argument("--x-factor", type=float, default=0.35,
                        help="when not requiring overlap, search x up to max(x_window, x_factor*k^3)")
    parser.add_argument("--x-window", type=int, default=320,
                        help="when not requiring overlap, also search x up to max(B)+x_window")
    parser.add_argument("--require-overlap", dest="require_overlap", action="store_true", default=True)
    parser.add_argument("--no-require-overlap", dest="require_overlap", action="store_false")
    parser.add_argument("--top", type=int, default=8)
    parser.add_argument("--output", default=os.path.join(RESULTS, "template_beam_156.json"))
    args = parser.parse_args()

    if args.k_max < len(args.B):
        parser.error("--k-max must be at least len(B)")
    if args.beam_width < 1:
        parser.error("--beam-width must be positive")

    data = run_beam(args)
    write_json(data, args.output)
    print_summary(data, args.top)
    print()
    print(f"Wrote {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
