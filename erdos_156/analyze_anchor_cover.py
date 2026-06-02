"""
Analyze a shifted-template as a dense-core plus anchor-cover system.

The script decomposes the relative blocker interval W(B) by source type:

  - core_core differences
  - core_anchor differences
  - anchor_anchor differences
  - midpoint blockers
  - template points themselves

This is for formula extraction: it explains how a fixed dense core and sparse
anchors cover a long interval.

Usage:
  python3 erdos_156/analyze_anchor_cover.py
"""
from __future__ import annotations

import argparse
import json
import os
from collections import Counter, defaultdict
from itertools import combinations
from typing import Iterable

import beam_template_search as beam


THIS_DIR = os.path.dirname(os.path.abspath(__file__))
RESULTS = os.path.join(THIS_DIR, "results")
DEFAULT_B = [
    0, 20, 35, 38, 39, 44, 46, 95, 132, 142,
    175, 267, 289, 301, 341, 410, 489, 594, 617, 681,
]
DEFAULT_CORE = [0, 20, 35, 38, 39, 44, 46]


def parse_int_list(raw: str) -> list[int]:
    vals = sorted(int(part.strip()) for part in raw.split(",") if part.strip())
    if len(vals) != len(set(vals)):
        raise argparse.ArgumentTypeError("values must be distinct")
    if not vals:
        raise argparse.ArgumentTypeError("list must be nonempty")
    return vals


def intervals(vals: Iterable[int]) -> list[list[int]]:
    return beam.intervals(vals)


def longest_prefix(values: Iterable[int], start: int = 1) -> list[int]:
    vals = set(values)
    out = []
    x = start
    while x in vals:
        out.append(x)
        x += 1
    return out


def classify_pair(a: int, b: int, core: set[int]) -> str:
    in_a = a in core
    in_b = b in core
    if in_a and in_b:
        return "core_core"
    if in_a or in_b:
        return "core_anchor"
    return "anchor_anchor"


def source_data(B: list[int], core: list[int]) -> dict:
    B = sorted(B)
    core_set = set(core)
    pair_for_diff = {}
    for a, b in combinations(B, 2):
        pair_for_diff[b - a] = (a, b)

    sources = defaultdict(list)
    for b in B:
        sources[b].append({"kind": "in_B", "anchor": b})

    for d, (u, v) in pair_for_diff.items():
        diff_type = classify_pair(u, v, core_set)
        for b in B:
            for sign, x in [("-", b - d), ("+", b + d)]:
                sources[x].append({
                    "kind": "diff",
                    "anchor": b,
                    "diff": d,
                    "sign": sign,
                    "pair": [u, v],
                    "diff_type": diff_type,
                })

    for a, b in combinations(B, 2):
        if (a + b) % 2 == 0:
            sources[(a + b) // 2].append({
                "kind": "midpoint",
                "pair": [a, b],
                "midpoint_type": classify_pair(a, b, core_set),
            })

    return {
        "sources": sources,
        "pair_for_diff": pair_for_diff,
    }


def summarize(B: list[int], core: list[int], interval: list[int] | None) -> dict:
    if not set(core).issubset(B):
        raise ValueError("core must be a subset of B")
    if not beam.is_sidon(B):
        raise ValueError("B is not Sidon")
    if not beam.is_sidon(core):
        raise ValueError("core is not Sidon")

    metric = beam.template_metric(B)
    if metric is None:
        raise ValueError("B has no admissible blocker interval")
    if interval is None:
        interval = metric["interval"]

    L, R = interval
    anchors = [x for x in B if x not in set(core)]
    data = source_data(B, core)
    sources = data["sources"]

    all_diffs = sorted(data["pair_for_diff"])
    core_diffs = sorted({b - a for a, b in combinations(core, 2)})
    anchor_diffs = sorted(
        d
        for d, (a, b) in data["pair_for_diff"].items()
        if a not in core or b not in core
    )
    small_prefix = longest_prefix(all_diffs)

    category_counts = Counter()
    primary_category_counts = Counter()
    anchor_hits = Counter()
    diff_hits = Counter()
    low_multiplicity = []
    uncovered = []
    core_diff_only_points = []

    for x in range(L, R + 1):
        srcs = sources.get(x, [])
        if not srcs:
            uncovered.append(x)
            continue
        cats = set()
        for src in srcs:
            if src["kind"] == "diff":
                cat = src["diff_type"]
                category_counts[cat] += 1
                anchor_hits[src["anchor"]] += 1
                diff_hits[src["diff"]] += 1
                cats.add(cat)
            else:
                category_counts[src["kind"]] += 1
                cats.add(src["kind"])
        for cat in cats:
            primary_category_counts[cat] += 1
        diff_srcs = [src for src in srcs if src["kind"] == "diff"]
        if len(diff_srcs) <= 2:
            low_multiplicity.append({
                "x": x,
                "diff_source_count": len(diff_srcs),
                "sources": srcs[:8],
            })
        if diff_srcs and all(src["diff_type"] == "core_core" for src in diff_srcs):
            core_diff_only_points.append(x)

    edge_points = list(range(L - 5, L + 6)) + list(range(R - 5, R + 6))
    edge_report = {
        str(x): sources.get(x, [])[:10]
        for x in edge_points
    }

    clusters = []
    current = [B[0]]
    for a, b in zip(B, B[1:]):
        if b - a <= 25:
            current.append(b)
        else:
            clusters.append(current)
            current = [b]
    clusters.append(current)

    return {
        "B": B,
        "core": core,
        "anchors": anchors,
        "k": len(B),
        "metric": metric,
        "analyzed_interval": interval,
        "all_diffs_count": len(all_diffs),
        "all_diffs_prefix_from_1": small_prefix,
        "core_diffs": core_diffs,
        "anchor_or_mixed_diffs_count": len(anchor_diffs),
        "clusters_gap_le_25": clusters,
        "uncovered_in_interval": uncovered,
        "source_event_counts": category_counts.most_common(),
        "point_coverage_counts_by_category": primary_category_counts.most_common(),
        "anchor_hits_top": anchor_hits.most_common(),
        "diff_hits_top": diff_hits.most_common(40),
        "low_multiplicity_sample": low_multiplicity[:40],
        "low_multiplicity_count": len(low_multiplicity),
        "core_diff_only_intervals": intervals(core_diff_only_points),
        "edge_sources": edge_report,
    }


def write_markdown(summary: dict, path: str) -> None:
    metric = summary["metric"]
    L, R = summary["analyzed_interval"]
    lines = [
        "# Anchor-cover analysis for Erdős #156",
        "",
        "## Template",
        "",
        f"- B: `{summary['B']}`",
        f"- Core: `{summary['core']}`",
        f"- Anchors: `{summary['anchors']}`",
        f"- Best interval: `{metric['interval']}`",
        f"- Covered N: `{metric['covered_N']}`",
        f"- Analyzed interval: `[{L},{R}]`",
        f"- Endpoint ratio: `{metric['covered_end_over_k3']:.6f}`",
        "",
        "## Difference structure",
        "",
        f"- Core differences: `{summary['core_diffs']}`",
        f"- Full difference prefix from 1: `{summary['all_diffs_prefix_from_1']}`",
        f"- Number of full differences: `{summary['all_diffs_count']}`",
        "",
        "## Source counts inside the interval",
        "",
        f"- Source event counts: `{summary['source_event_counts']}`",
        f"- Point coverage category counts: `{summary['point_coverage_counts_by_category']}`",
        f"- Low diff-multiplicity points: `{summary['low_multiplicity_count']}`",
        f"- Uncovered points in interval: `{summary['uncovered_in_interval']}`",
        "",
        "## Geometry",
        "",
        f"- Clusters with gap <= 25: `{summary['clusters_gap_le_25']}`",
        f"- Top anchor hits: `{summary['anchor_hits_top'][:12]}`",
        f"- Top difference hits: `{summary['diff_hits_top'][:20]}`",
        "",
        "## Edge behavior",
        "",
        "The interval is maximal because adjacent holes appear just outside it.",
        f"For this template, the analyzed interval is `[{L},{R}]`; inspect",
        "`edge_sources` in the JSON for the exact blockers around the two edges.",
    ]
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines).rstrip() + "\n")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--B", type=parse_int_list, default=DEFAULT_B)
    parser.add_argument("--core", type=parse_int_list, default=DEFAULT_CORE)
    parser.add_argument("--interval", type=parse_int_list, default=None,
                        help="optional L,R interval to analyze")
    parser.add_argument("--json-output", default=os.path.join(RESULTS, "anchor_cover_analysis_156.json"))
    parser.add_argument("--md-output", default=os.path.join(THIS_DIR, "anchor_cover_analysis.md"))
    args = parser.parse_args()

    if args.interval is not None and len(args.interval) != 2:
        parser.error("--interval must contain exactly two comma-separated integers")

    summary = summarize(args.B, args.core, args.interval)
    os.makedirs(os.path.dirname(args.json_output), exist_ok=True)
    with open(args.json_output, "w", encoding="utf-8") as fh:
        json.dump(summary, fh, indent=2)
    write_markdown(summary, args.md_output)

    metric = summary["metric"]
    print(json.dumps({
        "B": summary["B"],
        "core": summary["core"],
        "interval": metric["interval"],
        "covered_N": metric["covered_N"],
        "endpoint_ratio": metric["covered_end_over_k3"],
        "source_event_counts": summary["source_event_counts"],
        "anchor_hits_top": summary["anchor_hits_top"][:8],
        "outputs": [args.json_output, args.md_output],
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
