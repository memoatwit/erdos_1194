"""
Mine structural data from maximal Sidon witnesses for Erdős #156.

The useful reformulation is:

  x is blocked by existing differences iff x is in A +/- Delta(A).

Thus a small maximal Sidon set is close to a Sidon set A whose difference
translates cover [1,N].  This script measures that coverage for known
witnesses and writes a compact JSON/Markdown report.

Usage:
  python3 erdos_156/mine_structure.py
"""
from __future__ import annotations

import json
import math
import os
from collections import Counter, defaultdict
from itertools import combinations
from typing import Iterable


THIS_DIR = os.path.dirname(os.path.abspath(__file__))
RESULTS = os.path.join(THIS_DIR, "results")


def pair_diffs(A: list[int]) -> list[tuple[int, int, int]]:
    out = []
    for i, a in enumerate(A):
        for b in A[i + 1 :]:
            out.append((b - a, a, b))
    return sorted(out)


def is_sidon(A: list[int]) -> bool:
    diffs = [d for d, _, _ in pair_diffs(A)]
    return len(diffs) == len(set(diffs))


def coverage_sources(A: list[int], N: int) -> dict[int, list[tuple]]:
    sources: dict[int, list[tuple]] = defaultdict(list)
    for a in A:
        sources[a].append(("in_A", a))

    pairs = pair_diffs(A)
    for d, u, v in pairs:
        for a in A:
            lo = a - d
            hi = a + d
            if 1 <= lo <= N:
                sources[lo].append(("diff", a, d, u, v, "-"))
            if 1 <= hi <= N:
                sources[hi].append(("diff", a, d, u, v, "+"))

        s = u + v
        if s % 2 == 0:
            m = s // 2
            if 1 <= m <= N:
                sources[m].append(("midpoint", u, v))
    return sources


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


def compact_intervals(vals: Iterable[int], max_items: int = 12) -> str:
    parts = []
    for lo, hi in intervals(vals)[:max_items]:
        parts.append(str(lo) if lo == hi else f"{lo}-{hi}")
    extra = len(intervals(vals)) - max_items
    if extra > 0:
        parts.append(f"...(+{extra})")
    return ", ".join(parts) if parts else "-"


def witness_metrics(N: int, A: list[int], label: str) -> dict:
    A = sorted(A)
    sources = coverage_sources(A, N)
    all_points = set(range(1, N + 1))
    covered = set(sources)
    uncovered = sorted(all_points - covered)
    diff_covered = {
        x
        for x, srcs in sources.items()
        if any(src[0] == "diff" for src in srcs)
    }
    midpoint_only = sorted(
        x
        for x, srcs in sources.items()
        if x not in A
        and not any(src[0] == "diff" for src in srcs)
        and any(src[0] == "midpoint" for src in srcs)
    )
    diffs = pair_diffs(A)
    diff_values = [d for d, _, _ in diffs]
    gap_values = [b - a for a, b in zip(A, A[1:])]

    anchor_hits = Counter()
    diff_hits = Counter()
    essential_points = []
    for x, srcs in sources.items():
        diff_srcs = [src for src in srcs if src[0] == "diff"]
        for _, anchor, d, _u, _v, _sign in diff_srcs:
            anchor_hits[anchor] += 1
            diff_hits[d] += 1
        if len(diff_srcs) == 1 and x not in A:
            _, anchor, d, u, v, sign = diff_srcs[0]
            essential_points.append({
                "x": x,
                "anchor": anchor,
                "diff": d,
                "pair": [u, v],
                "sign": sign,
            })

    multiplicities = [len([src for src in srcs if src[0] == "diff"]) for srcs in sources.values()]
    multiplicities.sort()
    low_mult = [
        x
        for x in range(1, N + 1)
        if len([src for src in sources.get(x, []) if src[0] == "diff"]) <= 1
    ]

    return {
        "label": label,
        "N": N,
        "k": len(A),
        "A": A,
        "sidon": is_sidon(A),
        "span": A[-1] - A[0],
        "min": A[0],
        "max": A[-1],
        "gaps": gap_values,
        "tight_gaps": [g for g in gap_values if g <= 4],
        "densest_core4": densest_core(A, 4),
        "densest_core5": densest_core(A, 5),
        "normalized": [round(x / N, 4) for x in A],
        "diff_count": len(diff_values),
        "diff_min": min(diff_values),
        "diff_max": max(diff_values),
        "diffs": diff_values,
        "small_diffs": [d for d in diff_values if d <= 12],
        "large_diffs": [d for d in diff_values if d >= N - 20],
        "covered": len(covered),
        "uncovered": uncovered,
        "diff_covered": len(diff_covered),
        "midpoint_only": midpoint_only,
        "coverage_excess": sum(len(srcs) for srcs in sources.values()) - N,
        "diff_multiplicity_min": min(multiplicities) if multiplicities else 0,
        "diff_multiplicity_median": multiplicities[len(multiplicities) // 2] if multiplicities else 0,
        "diff_multiplicity_max": max(multiplicities) if multiplicities else 0,
        "low_diff_multiplicity_points": low_mult[:40],
        "anchor_hits": anchor_hits.most_common(),
        "diff_hits_top": diff_hits.most_common(12),
        "essential_diff_points": essential_points[:40],
        "essential_diff_count": len(essential_points),
    }


def densest_core(A: list[int], r: int) -> dict:
    best = None
    for core in combinations(A, r):
        diffs = [d for d, _, _ in pair_diffs(list(core))]
        small = [d for d in diffs if d <= 12]
        span = core[-1] - core[0]
        key = (span, -len(small), sum(core))
        if best is None or key < best[0]:
            best = (key, core, diffs, small)
    if best is None:
        return {}
    _key, core, diffs, small = best
    return {
        "core": list(core),
        "span": core[-1] - core[0],
        "gaps": [b - a for a, b in zip(core, core[1:])],
        "diffs": diffs,
        "small_diffs": small,
    }


def recursive_int_lists(obj) -> Iterable[list[int]]:
    if isinstance(obj, list):
        if obj and all(isinstance(x, int) for x in obj):
            yield list(obj)
        for x in obj:
            yield from recursive_int_lists(x)
    elif isinstance(obj, dict):
        for x in obj.values():
            yield from recursive_int_lists(x)


def load_witnesses() -> list[tuple[int, list[int], str]]:
    witnesses: list[tuple[int, list[int], str]] = []

    for name in sorted(os.listdir(RESULTS)):
        if not name.startswith("exact_156_N") or not name.endswith(".json"):
            continue
        path = os.path.join(RESULTS, name)
        with open(path, "r", encoding="utf-8") as fh:
            obj = json.load(fh)
        if obj.get("status") == "solved" and isinstance(obj.get("A"), list):
            witnesses.append((int(obj["N"]), list(obj["A"]), "exact"))
        for item in obj.get("log", []):
            if item.get("status") == "feasible" and isinstance(item.get("A"), list):
                witnesses.append((int(obj["N"]), list(item["A"]), item.get("method", "log")))

    frontier = os.path.join(RESULTS, "frontier_156_N125.json")
    if os.path.exists(frontier):
        with open(frontier, "r", encoding="utf-8") as fh:
            obj = json.load(fh)
        for key in ("upper_witness", "alternate_size8_witness"):
            if isinstance(obj.get(key), list):
                witnesses.append((int(obj["N"]), list(obj[key]), key))

    for name in sorted(os.listdir(RESULTS)):
        if not name.startswith("repair_156_N") or not name.endswith(".json"):
            continue
        path = os.path.join(RESULTS, name)
        with open(path, "r", encoding="utf-8") as fh:
            obj = json.load(fh)
        N = int(obj["N"])
        if obj.get("status") == "feasible" and isinstance(obj.get("best_A"), list):
            witnesses.append((N, list(obj["best_A"]), "repair"))
        alt = obj.get("alternate_verified_witness")
        if isinstance(alt, dict) and isinstance(alt.get("A"), list):
            witnesses.append((N, list(alt["A"]), "repair_alt"))

    # Deduplicate by (N,A) while keeping the first label.
    seen = set()
    unique = []
    for N, A, label in witnesses:
        key = (N, tuple(sorted(A)))
        if key in seen:
            continue
        seen.add(key)
        unique.append((N, sorted(A), label))
    return sorted(unique, key=lambda item: (item[0], len(item[1]), item[1]))


def write_markdown(metrics: list[dict], path: str) -> None:
    size8 = [m for m in metrics if m["k"] == 8 and m["N"] >= 105]
    lines = [
        "# Structural mining for Erdős #156",
        "",
        "This file mines known maximal Sidon witnesses as coverage objects.",
        "For a Sidon set `A`, an outside point is blocked by an existing difference",
        "exactly when it lies in `A +/- Delta(A)`.  Midpoint blockers are tracked",
        "separately.",
        "",
        "## Size-8 frontier witnesses",
        "",
        "| N | label | A | core4 | gaps | small diffs | diff cover | midpoint-only | median diff mult | essential diff points |",
        "|---:|---|---|---|---|---|---:|---|---:|---:|",
    ]
    for m in size8:
        lines.append(
            "| {N} | {label} | `{A}` | `{core}` | `{gaps}` | `{small}` | {diff_covered}/{N} | `{mid}` | {med} | {ess} |".format(
                N=m["N"],
                label=m["label"],
                A=m["A"],
                core=m["densest_core4"].get("core"),
                gaps=m["gaps"],
                small=m["small_diffs"],
                diff_covered=m["diff_covered"],
                mid=m["midpoint_only"],
                med=m["diff_multiplicity_median"],
                ess=m["essential_diff_count"],
            )
        )

    lines.extend([
        "",
        "## Observations",
        "",
        "1. The dominant blocker is `A +/- Delta(A)`.  The size-8 witnesses above",
        "   cover every point by translated existing differences except for at most",
        "   a few midpoint-only points.",
        "2. Tight adjacent or near-adjacent pairs are common but not universal.  They",
        "   create very small differences, which help cover neighborhoods around",
        "   every anchor.",
        "3. A recurring motif is a dense core of 4 or 5 marks plus one or two distant",
        "   anchors.  The core manufactures many small differences; the distant",
        "   anchors turn those differences into long-range coverage near the ends.",
        "4. The witnesses are not simple translates of one template.  Reflection and",
        "   shifting produce useful near-misses, but the successful sets vary in",
        "   where their tight pair and long anchor live.",
        "5. The right abstraction is likely a Sidon set whose difference set is a",
        "   sparse ruler and whose translates by the anchors form a bounded-overlap",
        "   cover of `[1,N]`.",
        "",
        "## Construction Hypothesis",
        "",
        "The data suggests trying to build \\(A\\) in two layers:",
        "",
        "1. Choose a small Sidon core \\(C\\) with many controlled small differences,",
        "   ideally a compact Golomb ruler whose difference set has short intervals",
        "   such as `{1,3,4}` or `{1,2,3,4,6,7}`.",
        "2. Add distant anchors \\(u,v,\\ldots\\) so the mixed differences",
        "   `u-C`, `v-C`, and `v-u` translate the core's local coverage across the",
        "   low and high ends of `[1,N]`.",
        "",
        "In this language, maximality is close to the covering condition",
        "",
        "```text",
        "[1,N] subset A + (A-A)",
        "```",
        "",
        "with a few leftover holes allowed if they are exact midpoints of pairs of",
        "elements of `A`.  A proof of Erdős #156 would need an infinite family of such",
        "integer Sidon sets with `|A| = O(N^(1/3))`.",
        "",
        "## Finite Template Found Overnight",
        "",
        "The clearest finite pattern so far is the 8-mark Golomb-ruler template",
        "",
        "```text",
        "B = [0, 40, 60, 61, 63, 67, 96, 112]",
        "gaps(B) = [40, 20, 1, 2, 4, 29, 16]",
        "```",
        "",
        "For every `N` from 120 through 144 inclusive, at least one shift",
        "`A = s + B` with `1 <= s <= 8` is a maximal Sidon subset of `[1,N]`.",
        "The same template fails at `N=145` by one addable point.  This is still",
        "finite data, but it is a more concrete object than the unrelated-looking",
        "individual witnesses.",
        "",
        "## Per-witness details",
        "",
    ])

    for m in size8:
        lines.extend([
            f"### N={m['N']} {m['label']}",
            "",
            f"- A: `{m['A']}`",
            f"- normalized: `{m['normalized']}`",
            f"- gaps: `{m['gaps']}`",
            f"- densest core4: `{m['densest_core4']}`",
            f"- densest core5: `{m['densest_core5']}`",
            f"- differences: `{m['diffs']}`",
            f"- coverage: `{m['covered']}/{m['N']}` total, `{m['diff_covered']}/{m['N']}` by existing differences",
            f"- midpoint-only points: `{m['midpoint_only']}`",
            f"- low diff-multiplicity points: `{compact_intervals(m['low_diff_multiplicity_points'])}`",
            f"- anchor hit counts: `{m['anchor_hits']}`",
            f"- top difference hit counts: `{m['diff_hits_top']}`",
            "",
        ])

    with open(path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines).rstrip() + "\n")


def main() -> int:
    witnesses = load_witnesses()
    metrics = [
        witness_metrics(N, A, label)
        for N, A, label in witnesses
        if is_sidon(A)
    ]
    json_path = os.path.join(RESULTS, "structure_156.json")
    md_path = os.path.join(THIS_DIR, "structure_mining.md")
    with open(json_path, "w", encoding="utf-8") as fh:
        json.dump(metrics, fh, indent=2)
    write_markdown(metrics, md_path)

    size8 = [m for m in metrics if m["k"] == 8 and m["N"] >= 105]
    summary = {
        "witnesses_analyzed": len(metrics),
        "size8_frontier_witnesses": len(size8),
        "size8_Ns": sorted({m["N"] for m in size8}),
        "min_diff_cover_fraction": min((m["diff_covered"] / m["N"] for m in size8), default=None),
        "max_midpoint_only": max((len(m["midpoint_only"]) for m in size8), default=None),
        "outputs": [json_path, md_path],
    }
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
