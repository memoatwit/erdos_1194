"""
Targeted repair search for #156 fixed-size witnesses.

This started as the N=125,k=8 repair search, but is now useful for arbitrary
N,k.  It searches the fixed-size Sidon landscape directly by maximizing the
number of blocked points.

Usage:
  python3 erdos_156/repair_125_k8.py 125 8 120 156
"""
from __future__ import annotations

import json
import os
import random
import sys
import time
from dataclasses import dataclass
from typing import Iterable


THIS_DIR = os.path.dirname(os.path.abspath(__file__))
RESULTS = os.path.join(THIS_DIR, "results")


def bit_for(x: int) -> int:
    return 1 << (x - 1)


def iter_bits(mask: int) -> Iterable[int]:
    while mask:
        low = mask & -mask
        yield low.bit_length()
        mask ^= low


def normalize(A: Iterable[int], N: int) -> tuple[int, ...] | None:
    vals = tuple(sorted(A))
    if len(vals) != len(set(vals)):
        return None
    if vals and (vals[0] < 1 or vals[-1] > N):
        return None
    return vals


def diff_mask(A: tuple[int, ...]) -> int | None:
    mask = 0
    for j, b in enumerate(A):
        for a in A[:j]:
            d = b - a
            bit = 1 << d
            if mask & bit:
                return None
            mask |= bit
    return mask


def is_sidon(A: tuple[int, ...], N: int) -> bool:
    vals = normalize(A, N)
    return vals is not None and diff_mask(vals) is not None


def blocked_mask(A: tuple[int, ...], N: int) -> int | None:
    """Return bit mask of points in [1,N] that cannot be added to A."""
    vals = normalize(A, N)
    if vals is None:
        return None

    blocked = 0
    for a in vals:
        blocked |= bit_for(a)

    diffs: list[int] = []
    seen_diffs = 0
    for j, b in enumerate(vals):
        for a in vals[:j]:
            d = b - a
            bit = 1 << d
            if seen_diffs & bit:
                return None
            seen_diffs |= bit
            diffs.append(d)
            s = a + b
            if s % 2 == 0:
                blocked |= bit_for(s // 2)

    for a in vals:
        for d in diffs:
            lo = a - d
            hi = a + d
            if 1 <= lo <= N:
                blocked |= bit_for(lo)
            if 1 <= hi <= N:
                blocked |= bit_for(hi)

    return blocked


def addable_points(A: tuple[int, ...], N: int) -> list[int]:
    mask = blocked_mask(A, N)
    if mask is None:
        return list(range(1, N + 1))
    full = (1 << N) - 1
    return list(iter_bits(full ^ mask))


def score(A: tuple[int, ...], N: int) -> int:
    mask = blocked_mask(A, N)
    return -1 if mask is None else mask.bit_count()


def profile(A: tuple[int, ...], N: int) -> dict:
    mask = blocked_mask(A, N)
    if mask is None:
        return {"blocked": -1, "addable": list(range(1, N + 1))}
    full = (1 << N) - 1
    addable = list(iter_bits(full ^ mask))
    return {
        "blocked": mask.bit_count(),
        "addable_count": len(addable),
        "addable": addable[:40],
    }


def legal_insertions(partial: tuple[int, ...], N: int) -> list[int]:
    vals = set(partial)
    out = []
    for x in range(1, N + 1):
        if x in vals:
            continue
        nxt = tuple(sorted((*partial, x)))
        if diff_mask(nxt) is not None:
            out.append(x)
    return out


def rank_one_swaps(
    A: tuple[int, ...],
    N: int,
    keep: int,
) -> list[tuple[int, tuple[int, ...]]]:
    """Return the best legal one-element replacement neighbors."""
    present = set(A)
    ranked: list[tuple[int, tuple[int, ...]]] = []
    for old in A:
        base = [x for x in A if x != old]
        for new in range(1, N + 1):
            if new in present:
                continue
            nxt = tuple(sorted((*base, new)))
            b = score(nxt, N)
            if b >= 0:
                ranked.append((b, nxt))
    ranked.sort(key=lambda item: (item[0], -sum(item[1])), reverse=True)
    return ranked[:keep]


def hill_climb(A: tuple[int, ...], N: int, deadline: float) -> tuple[int, ...]:
    """Greedy one-swap climb to a local optimum."""
    cur = A
    cur_score = score(cur, N)
    while time.time() < deadline:
        best = None
        for b, nxt in rank_one_swaps(cur, N, keep=1):
            if b > cur_score:
                best = (b, nxt)
                break
        if best is None:
            return cur
        cur_score, cur = best
        if cur_score == N:
            return cur
    return cur


def greedy_complete(
    partial: tuple[int, ...],
    N: int,
    k: int,
    rng: random.Random,
    top: int = 10,
) -> tuple[int, ...] | None:
    cur = tuple(sorted(partial))
    while len(cur) < k:
        cands = []
        for x in legal_insertions(cur, N):
            nxt = tuple(sorted((*cur, x)))
            span = nxt[-1] - nxt[0] if len(nxt) > 1 else 0
            center = -abs(2 * x - N - 1) / max(N, 1)
            val = score(nxt, N) + 0.03 * span + 0.05 * center + 0.001 * rng.random()
            cands.append((val, x))
        if not cands:
            return None
        cands.sort(reverse=True)
        _, x = rng.choice(cands[: min(top, len(cands))])
        cur = tuple(sorted((*cur, x)))
    return cur if diff_mask(cur) is not None else None


def random_sidon(N: int, k: int, rng: random.Random) -> tuple[int, ...] | None:
    partial: tuple[int, ...] = ()
    return greedy_complete(partial, N, k, rng, top=18)


def recursive_int_lists(obj) -> Iterable[list[int]]:
    if isinstance(obj, list):
        if obj and all(isinstance(x, int) for x in obj):
            yield list(obj)
        for x in obj:
            yield from recursive_int_lists(x)
    elif isinstance(obj, dict):
        for x in obj.values():
            yield from recursive_int_lists(x)


def seed_variants(raw: list[int], N: int, k: int) -> Iterable[tuple[int, ...]]:
    candidates: list[list[int]] = []
    if len(raw) == k:
        candidates.append(raw)
    elif len(raw) == k + 1:
        for i in range(len(raw)):
            candidates.append(raw[:i] + raw[i + 1 :])
    else:
        return

    for A in candidates:
        for base in (A, [N + 1 - x for x in A]):
            lo_shift = 1 - min(base)
            hi_shift = N - max(base)
            for shift in range(lo_shift, hi_shift + 1):
                vals = normalize((x + shift for x in base), N)
                if vals is not None and len(vals) == k and diff_mask(vals) is not None:
                    yield vals


def load_seeds(N: int, k: int) -> list[tuple[int, ...]]:
    raw_sets = [
        [43, 44, 56, 60, 75, 78, 86, 115],
        [1, 7, 51, 55, 58, 69, 84, 100],
        [1, 3, 43, 47, 53, 61, 66, 96],
        [17, 40, 43, 47, 56, 76, 78, 90],
        [11, 46, 50, 53, 59, 75, 83, 93],
        [1, 3, 13, 34, 47, 50, 58, 88],
        [18, 42, 51, 59, 71, 81, 86, 87, 118],
    ]

    if os.path.isdir(RESULTS):
        for name in os.listdir(RESULTS):
            if not name.endswith(".json"):
                continue
            path = os.path.join(RESULTS, name)
            try:
                with open(path, "r", encoding="utf-8") as fh:
                    obj = json.load(fh)
            except Exception:
                continue
            raw_sets.extend(recursive_int_lists(obj))

    seeds = set()
    for raw in raw_sets:
        for vals in seed_variants(raw, N, k):
            seeds.add(vals)
    return sorted(seeds, key=lambda A: (-score(A, N), A))


@dataclass
class SearchConfig:
    N: int = 125
    k: int = 8
    seconds: float = 120.0
    seed: int = 156
    beam_width: int = 160
    neighbor_keep: int = 12


def search(config: SearchConfig) -> dict:
    rng = random.Random(config.seed)
    t0 = time.time()
    deadline = t0 + config.seconds
    seen: dict[tuple[int, ...], int] = {}

    def add_state(A: tuple[int, ...] | None) -> None:
        if A is None or len(A) != config.k:
            return
        b = score(A, config.N)
        if b < 0:
            return
        old = seen.get(A)
        if old is None or b > old:
            seen[A] = b

    for A in load_seeds(config.N, config.k):
        add_state(hill_climb(A, config.N, deadline))
        if seen and max(seen.values()) == config.N:
            break
        if time.time() >= deadline:
            break

    while (
        len(seen) < config.beam_width
        and time.time() < deadline
        and (not seen or max(seen.values()) < config.N)
    ):
        add_state(random_sidon(config.N, config.k, rng))

    iterations = 0
    best_history = []
    last_report = t0

    while time.time() < deadline:
        iterations += 1
        beam = sorted(seen.items(), key=lambda item: (item[1], item[0]), reverse=True)
        beam = beam[: config.beam_width]
        best_A, best_b = beam[0]
        if not best_history or best_history[-1]["blocked"] != best_b:
            best_history.append({
                "iteration": iterations,
                "blocked": best_b,
                "A": list(best_A),
                "time_s": time.time() - t0,
            })
        if best_b == config.N:
            break

        if time.time() - last_report >= 10:
            print(
                f"progress iter={iterations} seen={len(seen)} "
                f"best_blocked={best_b} best_A={list(best_A)}",
                file=sys.stderr,
                flush=True,
            )
            last_report = time.time()

        for A, _ in beam:
            for _, nxt in rank_one_swaps(A, config.N, config.neighbor_keep):
                add_state(nxt)
                if score(nxt, config.N) == config.N or time.time() >= deadline:
                    break
            if time.time() >= deadline:
                break

        # Rebuild around good states.  This is the escape hatch from local
        # one-swap optima: keep 5-7 anchors, refill coverage-first.
        beam = sorted(seen.items(), key=lambda item: (item[1], item[0]), reverse=True)
        elite = [A for A, _ in beam[: min(60, len(beam))]]
        for _ in range(8 * max(1, len(elite))):
            if time.time() >= deadline:
                break
            parent = rng.choice(elite)
            drop = rng.choice([1, 1, 2, 2, 3])
            keep = tuple(x for x in parent if rng.random() > drop / config.k)
            if len(keep) > config.k - 1:
                keep = tuple(rng.sample(list(parent), config.k - drop))
            partial = tuple(sorted(keep))
            if diff_mask(partial) is None:
                continue
            child = greedy_complete(partial, config.N, config.k, rng, top=14)
            add_state(hill_climb(child, config.N, deadline) if child else None)

    ranked = sorted(seen.items(), key=lambda item: (item[1], item[0]), reverse=True)
    best_A, best_b = ranked[0]
    result = {
        "N": config.N,
        "k": config.k,
        "status": "feasible" if best_b == config.N else "not_found",
        "method": "seeded_one_swap_beam_repair",
        "seconds_requested": config.seconds,
        "time_s": time.time() - t0,
        "seed": config.seed,
        "states_seen": len(seen),
        "iterations": iterations,
        "best_blocked": best_b,
        "best_A": list(best_A),
        "best_profile": profile(best_A, config.N),
        "best_history": best_history[-12:],
        "top_near_misses": [
            {
                "blocked": b,
                "A": list(A),
                "addable": addable_points(A, config.N)[:20],
            }
            for A, b in ranked[:10]
        ],
    }
    return result


def main(argv: list[str]) -> int:
    N = int(argv[1]) if len(argv) > 1 else 125
    k = int(argv[2]) if len(argv) > 2 else 8
    seconds = float(argv[3]) if len(argv) > 3 else 120.0
    seed = int(argv[4]) if len(argv) > 4 else 156
    result = search(SearchConfig(N=N, k=k, seconds=seconds, seed=seed))
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
