#!/usr/bin/env python3
"""Mine the structure of surviving UNKNOWN chunks in the r_3(212) search.

Given one or more JSONL files of broad/refinement results, this script:

  1. Compares UNKNOWN rows against INFEASIBLE rows on the same scope.
  2. Computes per-split-variable IN/OUT enrichment for UNKs.
  3. Mines enriched pairs/triples of split-variable assignments.
  4. Profiles the hot middle window [67, 91] cardinality and other intervals.
  5. Hamming-clusters the UNK fixed-in sets and reports cluster sizes.
  6. Emits a structured report (JSON + human-readable text).

The script is read-only and stdlib-only.  It is meant to answer:
"Is there a clean structural pattern that distinguishes the surviving UNK
chunks from INFEASIBLE chunks?"  If a small handful of features cleanly
separate them, that suggests a new pruning constraint exists.  If the
features look diffuse, the hard pocket is genuinely fractal.

Typical usage:

    python3 r3_mine_unknowns.py \
        --input results/N212_K44_window100k_recap300_sample100.jsonl \
        --label recap300 \
        --out-json results/r3_unk_structure_recap300.json \
        --out-report results/r3_unk_structure_recap300.txt

    # Compare two populations:
    python3 r3_mine_unknowns.py \
        --input results/N212_K44_window100k_recap120_sample100.jsonl --label recap120 \
        --input results/N212_K44_window100k_recap300_sample100.jsonl --label recap300 \
        --out-report results/r3_unk_structure_compare.txt
"""

from __future__ import annotations

import argparse
import json
import math
import statistics
from collections import Counter, defaultdict
from itertools import combinations
from pathlib import Path

# ---------------------------------------------------------------------------
# Reference constants
# ---------------------------------------------------------------------------

# Hot middle window — flagged as the structural hotspot by prior profiling.
DEFAULT_HOT_WINDOW = (67, 91)

# Witness for r_3(212) ≥ 43 (verified).
DEFAULT_WITNESS = [
    3, 4, 9, 11, 12, 16, 22, 24, 25, 27, 31, 48, 52, 54, 55, 57, 63, 67, 68,
    70, 75, 76, 91, 142, 145, 150, 152, 156, 161, 164, 165, 168, 181, 182,
    187, 189, 190, 195, 202, 204, 205, 207, 211,
]

# Split-vars file in degree order (positions 0..23 are the broad split).
SPLIT_VARS_DEGREE_ORDER = [
    91, 76, 75, 142, 70, 68, 145, 67, 63, 150, 152, 57, 156, 55, 54, 52,
    161, 164, 48, 165, 168, 181, 31, 182, 27, 187, 25, 24, 189, 190, 22,
    195, 16, 12, 11, 202, 9, 204, 205, 207, 4, 3, 211,
]
BROAD_SPLIT_DEPTH = 24


# ---------------------------------------------------------------------------
# I/O
# ---------------------------------------------------------------------------


def iter_jsonl(path: str | Path):
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                yield json.loads(line)
            except json.JSONDecodeError:
                continue


def load_rows(paths: list[str]) -> list[dict]:
    rows: list[dict] = []
    for p in paths:
        for r in iter_jsonl(p):
            rows.append(r)
    return rows


# ---------------------------------------------------------------------------
# Statistics helpers
# ---------------------------------------------------------------------------


def fmt_pct(x: float) -> str:
    return f"{100.0 * x:.2f}%"


def fisher_log_odds(a: int, b: int, c: int, d: int) -> float:
    """log-odds with 0.5 smoothing.  a=UNK-with-feature, b=UNK-without,
    c=INF-with-feature, d=INF-without.  Positive ⇒ feature enriched in UNK."""
    a += 0.5
    b += 0.5
    c += 0.5
    d += 0.5
    return math.log((a / b) / (c / d))


# ---------------------------------------------------------------------------
# Feature extraction
# ---------------------------------------------------------------------------


def split_pin_vector(row: dict) -> tuple[tuple[int, int], ...]:
    """Return a tuple of (value, 1-if-in-else-0) for each broad-split witness
    value present in the row.  Only includes values from SPLIT_VARS_DEGREE_ORDER
    up to BROAD_SPLIT_DEPTH."""
    fixed_in = set(int(v) for v in row.get("fixed_in", []))
    fixed_out = set(int(v) for v in row.get("fixed_out", []))
    pins: list[tuple[int, int]] = []
    for value in SPLIT_VARS_DEGREE_ORDER[:BROAD_SPLIT_DEPTH]:
        if value in fixed_in:
            pins.append((value, 1))
        elif value in fixed_out:
            pins.append((value, 0))
    return tuple(pins)


def fixed_in_set(row: dict) -> set[int]:
    return {int(v) for v in row.get("fixed_in", [])}


def fixed_out_set(row: dict) -> set[int]:
    return {int(v) for v in row.get("fixed_out", [])}


def hot_window_in_count(row: dict, lo: int, hi: int) -> int:
    fi = fixed_in_set(row)
    return sum(1 for v in fi if lo <= v <= hi)


def hot_window_out_count(row: dict, lo: int, hi: int) -> int:
    fo = fixed_out_set(row)
    return sum(1 for v in fo if lo <= v <= hi)


def hamming_distance(a: set[int], b: set[int]) -> int:
    return len(a ^ b)


# ---------------------------------------------------------------------------
# Single-pin enrichment
# ---------------------------------------------------------------------------


def single_pin_enrichment(unks: list[dict], infs: list[dict]) -> list[dict]:
    """For each split-value, compute UNK-vs-INF base rates of IN/OUT."""
    counts: dict[int, dict[str, dict[str, int]]] = {}
    for label, rows in (("UNK", unks), ("INF", infs)):
        for row in rows:
            fi = fixed_in_set(row)
            fo = fixed_out_set(row)
            for value in SPLIT_VARS_DEGREE_ORDER[:BROAD_SPLIT_DEPTH]:
                c = counts.setdefault(value, {
                    "UNK": {"in": 0, "out": 0, "unknown": 0},
                    "INF": {"in": 0, "out": 0, "unknown": 0},
                })
                if value in fi:
                    c[label]["in"] += 1
                elif value in fo:
                    c[label]["out"] += 1
                else:
                    c[label]["unknown"] += 1
    out: list[dict] = []
    n_unk = len(unks)
    n_inf = len(infs)
    for value, c in counts.items():
        unk_in = c["UNK"]["in"]
        unk_out = c["UNK"]["out"]
        inf_in = c["INF"]["in"]
        inf_out = c["INF"]["out"]
        # Enrichment "feature = OUT".
        a, b = unk_out, unk_in
        d_, c_ = inf_in, inf_out  # rename to fit fisher_log_odds convention
        log_odds_out = fisher_log_odds(a, b, c_, d_)
        unk_out_rate = unk_out / n_unk if n_unk else 0.0
        inf_out_rate = inf_out / n_inf if n_inf else 0.0
        out.append({
            "value": value,
            "unk_in": unk_in, "unk_out": unk_out,
            "inf_in": inf_in, "inf_out": inf_out,
            "unk_out_rate": unk_out_rate,
            "inf_out_rate": inf_out_rate,
            "log_odds_out_minus_in": log_odds_out,
        })
    out.sort(key=lambda r: -abs(r["log_odds_out_minus_in"]))
    return out


# ---------------------------------------------------------------------------
# Pair / triple co-occurrence
# ---------------------------------------------------------------------------


def k_pin_enrichment(
    unks: list[dict],
    infs: list[dict],
    k: int,
    top_n: int = 25,
) -> list[dict]:
    """Find k-tuples of (value, IN/OUT) most enriched in UNK vs INF."""
    def feature_counter(rows: list[dict]) -> Counter:
        counter: Counter = Counter()
        for row in rows:
            v = split_pin_vector(row)
            if len(v) < k:
                continue
            for combo in combinations(v, k):
                counter[combo] += 1
        return counter

    unk_counts = feature_counter(unks)
    inf_counts = feature_counter(infs)
    n_unk = len(unks)
    n_inf = len(infs)

    rows: list[dict] = []
    for combo, cnt in unk_counts.items():
        unk_with = cnt
        unk_without = n_unk - cnt
        inf_with = inf_counts.get(combo, 0)
        inf_without = n_inf - inf_with
        if unk_with < max(2, n_unk // 20):
            continue  # require at least 5% support in UNK
        lo = fisher_log_odds(unk_with, unk_without, inf_with, inf_without)
        rows.append({
            "pattern": [{"value": v, "state": "IN" if s == 1 else "OUT"} for v, s in combo],
            "unk_with": unk_with,
            "unk_without": unk_without,
            "inf_with": inf_with,
            "inf_without": inf_without,
            "unk_rate": unk_with / n_unk if n_unk else 0.0,
            "inf_rate": inf_with / n_inf if n_inf else 0.0,
            "log_odds": lo,
        })
    rows.sort(key=lambda r: -r["log_odds"])
    return rows[:top_n]


# ---------------------------------------------------------------------------
# Window cardinality profile
# ---------------------------------------------------------------------------


def window_cardinality_profile(rows: list[dict], lo: int, hi: int) -> dict:
    in_counts = [hot_window_in_count(r, lo, hi) for r in rows]
    out_counts = [hot_window_out_count(r, lo, hi) for r in rows]
    return {
        "window": [lo, hi],
        "in_count_distribution": dict(Counter(in_counts)),
        "out_count_distribution": dict(Counter(out_counts)),
        "in_mean": statistics.fmean(in_counts) if in_counts else 0.0,
        "out_mean": statistics.fmean(out_counts) if out_counts else 0.0,
    }


# ---------------------------------------------------------------------------
# Hamming clustering
# ---------------------------------------------------------------------------


def hamming_cluster(rows: list[dict], threshold: int = 2) -> list[list[int]]:
    """Greedy single-linkage cluster by Hamming distance of fixed_in ⊕ fixed_out
    over the broad split vars only.  Returns list of clusters (list of row idx)."""
    universe = set(SPLIT_VARS_DEGREE_ORDER[:BROAD_SPLIT_DEPTH])
    vectors: list[set[int]] = []
    for r in rows:
        # Use fixed_in restricted to the broad split vars.
        v = fixed_in_set(r) & universe
        vectors.append(v)
    n = len(vectors)
    parent = list(range(n))

    def find(x: int) -> int:
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(x: int, y: int) -> None:
        rx, ry = find(x), find(y)
        if rx != ry:
            parent[rx] = ry

    for i in range(n):
        for j in range(i + 1, n):
            if hamming_distance(vectors[i], vectors[j]) <= threshold:
                union(i, j)

    clusters: dict[int, list[int]] = defaultdict(list)
    for i in range(n):
        clusters[find(i)].append(i)
    return sorted(clusters.values(), key=lambda c: -len(c))


# ---------------------------------------------------------------------------
# Reporting
# ---------------------------------------------------------------------------


def render_text_report(payload: dict) -> str:
    lines: list[str] = []
    lines.append("r_3(212) hard-pocket structural mining report")
    lines.append("=" * 60)
    for pop in payload["populations"]:
        lines.append("")
        lines.append(f"Population: {pop['label']}")
        lines.append("-" * 60)
        lines.append(f"  paths       : {pop['paths']}")
        lines.append(f"  total rows  : {pop['n_rows']}")
        lines.append(f"  UNK rows    : {pop['n_unk']}")
        lines.append(f"  INF rows    : {pop['n_inf']}")
        lines.append(f"  FEAS rows   : {pop['n_feas']}")

        lines.append("")
        lines.append("  Top single-pin enrichment (|log-odds| OUT vs IN):")
        for r in pop["single_pin"][:10]:
            lines.append(
                f"    value {r['value']:>3}  UNK out={fmt_pct(r['unk_out_rate']):>8}  "
                f"INF out={fmt_pct(r['inf_out_rate']):>8}  log-odds={r['log_odds_out_minus_in']:+.3f}"
            )

        for k_label, k_key in (("pair", "pairs"), ("triple", "triples")):
            k_rows = pop.get(k_key, [])
            if not k_rows:
                continue
            lines.append("")
            lines.append(f"  Top {k_label} co-occurrence enrichment (UNK vs INF):")
            for r in k_rows[:8]:
                pat = ",".join(f"{p['value']}={p['state']}" for p in r["pattern"])
                lines.append(
                    f"    [{pat}]  UNK={fmt_pct(r['unk_rate']):>7}  "
                    f"INF={fmt_pct(r['inf_rate']):>7}  log-odds={r['log_odds']:+.3f}"
                )

        lines.append("")
        lines.append(f"  Hot window {pop['hot_window']} cardinality:")
        lines.append(f"    UNK fixed_in mean : {pop['hot_window_unk']['in_mean']:.2f}")
        lines.append(f"    UNK fixed_in dist : {pop['hot_window_unk']['in_count_distribution']}")
        lines.append(f"    UNK fixed_out mean: {pop['hot_window_unk']['out_mean']:.2f}")
        lines.append(f"    INF fixed_in mean : {pop['hot_window_inf']['in_mean']:.2f}")
        lines.append(f"    INF fixed_out mean: {pop['hot_window_inf']['out_mean']:.2f}")

        if pop.get("clusters"):
            lines.append("")
            lines.append("  UNK Hamming clusters (size ≥ 2):")
            for i, c in enumerate(pop["clusters"][:8]):
                lines.append(f"    cluster {i}: size={c['size']}, members={c['member_chunk_ids'][:8]}{'…' if c['size']>8 else ''}")
    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def profile_population(
    *,
    label: str,
    paths: list[str],
    hot_window: tuple[int, int],
) -> dict:
    rows = load_rows(paths)
    unks = [r for r in rows if r.get("status") == "UNKNOWN"]
    infs = [r for r in rows if r.get("status") == "INFEASIBLE"]
    feas = [r for r in rows if r.get("status") == "FEASIBLE"]

    single = single_pin_enrichment(unks, infs)
    pairs = k_pin_enrichment(unks, infs, k=2)
    triples = k_pin_enrichment(unks, infs, k=3, top_n=15) if len(unks) >= 10 else []

    hot_unk = window_cardinality_profile(unks, *hot_window)
    hot_inf = window_cardinality_profile(infs, *hot_window)

    clusters_raw = hamming_cluster(unks, threshold=2) if len(unks) >= 2 else []
    clusters = []
    for cluster in clusters_raw:
        if len(cluster) < 2:
            continue
        chunk_ids = [unks[i].get("chunk_id") for i in cluster]
        clusters.append({"size": len(cluster), "member_chunk_ids": chunk_ids})

    return {
        "label": label,
        "paths": paths,
        "n_rows": len(rows),
        "n_unk": len(unks),
        "n_inf": len(infs),
        "n_feas": len(feas),
        "hot_window": list(hot_window),
        "single_pin": single,
        "pairs": pairs,
        "triples": triples,
        "hot_window_unk": hot_unk,
        "hot_window_inf": hot_inf,
        "clusters": clusters,
    }


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--input", action="append", required=True,
                   help="JSONL input file (may be repeated; each --input pairs with the following --label).")
    p.add_argument("--label", action="append", required=True,
                   help="Population label.  Number must match --input count.")
    p.add_argument("--hot-window", type=str, default=f"{DEFAULT_HOT_WINDOW[0]},{DEFAULT_HOT_WINDOW[1]}",
                   help="Inclusive [LO,HI] of the hot middle window.")
    p.add_argument("--out-json", type=Path, default=None)
    p.add_argument("--out-report", type=Path, default=None)
    args = p.parse_args()

    if len(args.input) != len(args.label):
        p.error("Number of --input flags must equal number of --label flags.")
    lo, hi = (int(x) for x in args.hot_window.split(","))

    populations = []
    for label, path in zip(args.label, args.input):
        populations.append(profile_population(
            label=label, paths=[path], hot_window=(lo, hi),
        ))

    payload = {"populations": populations, "hot_window": [lo, hi]}

    if args.out_json:
        args.out_json.parent.mkdir(parents=True, exist_ok=True)
        with args.out_json.open("w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)
    if args.out_report:
        args.out_report.parent.mkdir(parents=True, exist_ok=True)
        with args.out_report.open("w", encoding="utf-8") as f:
            f.write(render_text_report(payload))

    # Also print the report to stdout.
    print(render_text_report(payload))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
