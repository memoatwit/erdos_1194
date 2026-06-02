"""
Exact branch-and-bound decision solver for r_3(N).

This is a lightweight fallback to CP-SAT for fixed-cardinality infeasibility
checks.  It keeps a current AP-free selected set R and a candidate mask P.
Adding v removes every w where some already-selected s makes {s,v,w} a
3-term AP.  A greedy coloring of the current pairwise compatibility graph gives
an upper bound on how many more points can be added.
"""
from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

from r3_cpsat import load_int_set
from r3_verify import verify


def bit(value: int) -> int:
    return 1 << (value - 1)


def iter_bits(mask: int):
    while mask:
        low = mask & -mask
        yield low.bit_length()
        mask ^= low


def build_forbid_pair(N: int) -> list[list[int]]:
    forbid = [[0] * (N + 1) for _ in range(N + 1)]
    for a in range(1, N + 1):
        for b in range(a + 1, N + 1):
            values = set()
            c = 2 * b - a
            if 1 <= c <= N:
                values.add(c)
            c = 2 * a - b
            if 1 <= c <= N:
                values.add(c)
            if (a + b) % 2 == 0:
                c = (a + b) // 2
                if 1 <= c <= N:
                    values.add(c)
            mask = 0
            for c in values:
                if c not in (a, b):
                    mask |= bit(c)
            forbid[a][b] = mask
            forbid[b][a] = mask
    return forbid


def ap_count_degrees(N: int) -> list[int]:
    degrees = [0] * (N + 1)
    for b in range(1, N + 1):
        max_d = min(b - 1, N - b)
        for d in range(1, max_d + 1):
            for value in (b - d, b, b + d):
                degrees[value] += 1
    return degrees


class R3BranchBound:
    def __init__(self, N: int, target: int, fixed_in: list[int], fixed_out: list[int], time_limit: float | None):
        self.N = N
        self.target = target
        self.fixed_in = sorted(set(fixed_in))
        self.fixed_out = sorted(set(fixed_out))
        self.forbid = build_forbid_pair(N)
        self.degrees = ap_count_degrees(N)
        self.time_limit = time_limit
        self.started = time.time()
        self.nodes = 0
        self.prunes_bound = 0
        self.prunes_cardinality = 0
        self.timed_out = False
        self.best_size = len(self.fixed_in)
        self.best_witness = list(self.fixed_in)

    def timeout(self) -> bool:
        if self.time_limit is None:
            return False
        if time.time() - self.started > self.time_limit:
            self.timed_out = True
            return True
        return False

    def block_mask(self, value: int, selected: tuple[int, ...]) -> int:
        out = 0
        for s in selected:
            out |= self.forbid[value][s]
        return out

    def choose_vertex(self, mask: int, selected: tuple[int, ...], candidates: int) -> int:
        best = None
        best_key = None
        for value in iter_bits(mask):
            compat = candidates & ~self.block_mask(value, selected) & ~bit(value)
            key = (self.degrees[value], -compat.bit_count(), -abs(value - (self.N + 1) / 2), -value)
            if best_key is None or key > best_key:
                best = value
                best_key = key
        assert best is not None
        return best

    def color_sort(self, candidates: int, selected: tuple[int, ...]) -> tuple[list[int], list[int]]:
        order: list[int] = []
        colors: list[int] = []
        uncolored = candidates
        color = 0
        while uncolored:
            color += 1
            available = uncolored
            while available:
                value = self.choose_vertex(available, selected, candidates)
                value_bit = bit(value)
                order.append(value)
                colors.append(color)
                uncolored &= ~value_bit
                available &= ~value_bit
                compatible = candidates & ~self.block_mask(value, selected) & ~value_bit
                available &= ~compatible
        return order, colors

    def initial_candidates(self) -> int | None:
        report = verify(self.fixed_in, N=self.N)
        if not report.get("ok"):
            return None
        fixed_in_mask = 0
        for value in self.fixed_in:
            fixed_in_mask |= bit(value)
        fixed_out_mask = 0
        for value in self.fixed_out:
            fixed_out_mask |= bit(value)
        all_mask = (1 << self.N) - 1
        candidates = all_mask & ~fixed_in_mask & ~fixed_out_mask
        selected = tuple(self.fixed_in)
        for value in self.fixed_in:
            candidates &= ~self.block_mask(value, tuple(x for x in selected if x != value))
        return candidates

    def search(self) -> list[int] | None:
        candidates = self.initial_candidates()
        if candidates is None:
            return None
        return self.expand(tuple(self.fixed_in), candidates)

    def expand(self, selected: tuple[int, ...], candidates: int) -> list[int] | None:
        self.nodes += 1
        if self.nodes % 20000 == 0 and self.timeout():
            return None
        selected_size = len(selected)
        if selected_size > self.best_size:
            self.best_size = selected_size
            self.best_witness = sorted(selected)
        if selected_size >= self.target:
            witness = sorted(selected)
            if verify(witness, N=self.N).get("ok"):
                return witness
            return None
        if selected_size + candidates.bit_count() < self.target:
            self.prunes_cardinality += 1
            return None

        order, colors = self.color_sort(candidates, selected)
        while order:
            if self.timeout():
                return None
            value = order.pop()
            color = colors.pop()
            if selected_size + color < self.target:
                self.prunes_bound += 1
                return None
            value_bit = bit(value)
            candidates &= ~value_bit
            next_candidates = candidates & ~self.block_mask(value, selected)
            result = self.expand(tuple(sorted((*selected, value))), next_candidates)
            if result is not None:
                return result
        return None


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--N", type=int, required=True)
    parser.add_argument("--K", type=int, required=True)
    parser.add_argument("--fix-in", type=Path, default=None)
    parser.add_argument("--fix-out", type=Path, default=None)
    parser.add_argument("--time-limit", type=float, default=None)
    parser.add_argument("--output", type=Path, default=None)
    args = parser.parse_args()

    fixed_in = load_int_set(args.fix_in) if args.fix_in else []
    fixed_out = load_int_set(args.fix_out) if args.fix_out else []
    overlap = sorted(set(fixed_in) & set(fixed_out))
    if overlap:
        parser.error(f"fixed sets overlap: {overlap[:10]}")

    solver = R3BranchBound(args.N, args.K, fixed_in, fixed_out, args.time_limit)
    witness = solver.search()
    if witness is not None:
        status = "FEASIBLE"
    elif solver.timed_out:
        status = "UNKNOWN"
    else:
        status = "INFEASIBLE"
    result = {
        "N": args.N,
        "K": args.K,
        "status": status,
        "seconds": round(time.time() - solver.started, 4),
        "nodes": solver.nodes,
        "best_size": solver.best_size,
        "best_witness": solver.best_witness,
        "fixed_in": fixed_in,
        "fixed_out": fixed_out,
        "prunes_bound": solver.prunes_bound,
        "prunes_cardinality": solver.prunes_cardinality,
        "witness": witness or [],
        "witness_verified": bool(witness and verify(witness, N=args.N).get("ok")),
    }
    print(json.dumps(result, sort_keys=True))
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with args.output.open("w", encoding="utf-8") as fh:
            json.dump(result, fh, indent=2, sort_keys=True)
            fh.write("\n")
    return 0 if status != "UNKNOWN" else 1


if __name__ == "__main__":
    raise SystemExit(main())
