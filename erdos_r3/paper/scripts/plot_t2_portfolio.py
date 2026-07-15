#!/usr/bin/env python3
"""Plot the two-stage T2 CDCL portfolio from released JSONL shards."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter


def load_rows(directory: Path, pattern: str) -> list[dict]:
    rows: list[dict] = []
    for path in sorted(directory.glob(pattern)):
        for line in path.read_text().splitlines():
            if line.strip():
                rows.append(json.loads(line))
    return rows


def plot_cactus(ax, rows: list[dict], *, expected: int, cap: float, color: str, title: str) -> None:
    if len(rows) != expected:
        raise ValueError(f"{title}: expected {expected} rows, found {len(rows)}")
    sat = [row for row in rows if row["status"] == "SAT"]
    if sat:
        raise ValueError(f"{title}: SAT rows require witness verification")

    solved = sorted(float(row["solver_seconds"]) for row in rows if row["status"] == "UNSAT")
    unknown = sum(row["status"] == "UNKNOWN" for row in rows)
    if len(solved) + unknown != expected:
        raise ValueError(f"{title}: unexpected status values")

    ranks = range(1, len(solved) + 1)
    ax.plot(ranks, solved, color=color, linewidth=1.8)
    ax.axhline(cap, color="#555555", linewidth=0.9, linestyle=(0, (4, 3)))
    ax.axvline(len(solved), color=color, linewidth=0.9, linestyle=(0, (2, 3)))
    ax.text(
        0.03,
        0.94,
        f"{len(solved):,}/{expected:,} UNSAT\n{unknown:,} UNKNOWN at cap",
        transform=ax.transAxes,
        ha="left",
        va="top",
        fontsize=8.5,
        color="#222222",
    )
    ax.set_title(title, fontsize=10.5, loc="left", pad=8)
    ax.set_xlim(0, expected * 1.015)
    ax.set_yscale("log")
    ax.set_ylim(1, cap * 1.35)
    ax.set_xlabel("Instances closed UNSAT")
    ax.grid(axis="y", color="#d9d9d9", linewidth=0.6)
    ax.spines[["top", "right"]].set_visible(False)
    ax.tick_params(labelsize=8.5)
    ax.xaxis.set_major_formatter(FuncFormatter(lambda value, _: f"{int(value):,}"))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--kissat-dir", type=Path, required=True)
    parser.add_argument("--cadical-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--png", type=Path)
    args = parser.parse_args()

    kissat = load_rows(args.kissat_dir, "t2_kissat_idx*.jsonl")
    cadical = load_rows(args.cadical_dir, "cadical_idx*.jsonl")

    plt.rcParams.update(
        {
            "font.family": "serif",
            "font.size": 9,
            "axes.edgecolor": "#333333",
            "axes.labelcolor": "#222222",
            "xtick.color": "#333333",
            "ytick.color": "#333333",
            "figure.facecolor": "white",
            "axes.facecolor": "white",
        }
    )
    fig, axes = plt.subplots(1, 2, figsize=(7.25, 3.15), sharey=True)
    plot_cactus(
        axes[0],
        kissat,
        expected=6071,
        cap=7200,
        color="#1f5a85",
        title="(a) kissat 4.0.4 on all T2 chunks",
    )
    plot_cactus(
        axes[1],
        cadical,
        expected=112,
        cap=43200,
        color="#b85c26",
        title="(b) CaDiCaL 3.0.0 on kissat residual",
    )
    axes[0].set_ylabel("Solver time (seconds, log scale)")
    fig.tight_layout(w_pad=2.0)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(args.output, bbox_inches="tight")
    if args.png:
        fig.savefig(args.png, dpi=220, bbox_inches="tight")


if __name__ == "__main__":
    main()
