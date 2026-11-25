#!/usr/bin/env python3
"""Create a two-panel Figure 7 comparison: corrected data left, old data right."""

from __future__ import annotations

import csv
import math
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np


HERE = Path(__file__).resolve().parent
CORRECTED = HERE / "timing_data.csv"
OLD = HERE / "reference_timing_data.csv"
OUTPUT = HERE / "Figure-7-corrected-vs-old.pdf"
COLORS = {"LDA": "#0072B2", "HSE06": "#E69F00"}
MARKERS = {"4x4x4": "s", "8x8x8": "o"}
CORE_TICKS = (128, 256, 512, 1024, 2048)


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="") as handle:
        return list(csv.DictReader(handle))


def fit(rows: list[dict[str, str]], x_key: str, y_key: str) -> tuple[float, float]:
    x = np.log([float(row[x_key]) for row in rows])
    y = np.log([float(row[y_key]) for row in rows])
    slope, intercept = np.polyfit(x, y, 1)
    return math.exp(intercept), float(slope)


def corrected_series(rows: list[dict[str, str]], supercell: str, functional: str) -> list[dict[str, str]]:
    return sorted(
        [row for row in rows if row["supercell"] == supercell and row["functional"] == functional],
        key=lambda row: int(row["cores"]),
    )


def old_series(rows: list[dict[str, str]], supercell: str, functional: str) -> list[dict[str, str]]:
    selected = {"4x4x4": "4x4x4_lda_p3422" if functional == "LDA" else "4x4x4_hse06_p3422",
                "8x8x8": "8x8x8_lda_p3211" if functional == "LDA" else "8x8x8_hse06_p3211"}[supercell]
    return sorted([row for row in rows if row["series_id"] == selected], key=lambda row: int(row["cores"]))


def plot_panel(axis: plt.Axes, rows: list[dict[str, str]], corrected: bool) -> None:
    for supercell in ("4x4x4", "8x8x8"):
        for functional in ("LDA", "HSE06"):
            subset = corrected_series(rows, supercell, functional) if corrected else old_series(rows, supercell, functional)
            if not subset:
                continue
            x_key = "cores"
            y_key = "polarization_seconds" if corrected else "polarization_time_s"
            x = np.array([int(row[x_key]) for row in subset], dtype=float)
            y = np.array([float(row[y_key]) for row in subset], dtype=float)
            amplitude, exponent = fit(subset, x_key, y_key)
            color = COLORS[functional]
            marker = MARKERS[supercell]
            axis.scatter(x, y, color=color, marker=marker, edgecolor="black", linewidth=0.4, s=28)
            fit_x = np.geomspace(x.min(), x.max(), 200)
            axis.plot(fit_x, amplitude * fit_x**exponent, color=color, linestyle="--", linewidth=0.9)
            axis.text(
                0.04 if supercell == "4x4x4" else 0.64,
                0.16 if functional == "LDA" else 0.28,
                fr"{supercell}, {functional}: $m={exponent:.2f}$",
                transform=axis.transAxes,
                color=color,
                fontsize=7,
            )

    axis.set_xscale("log", base=2)
    axis.set_yscale("log")
    axis.set_xlim(110, 2300)
    axis.set_xticks(CORE_TICKS)
    axis.get_xaxis().set_major_formatter(plt.ScalarFormatter())
    axis.grid(axis="y", color="0.82", linewidth=0.5)
    xmin, xmax = axis.get_xlim()
    ymin, ymax = axis.get_ylim()
    for constant in np.logspace(np.log10(xmin * ymin), np.log10(xmax * ymax), 8):
        axis.plot([xmin, xmax], [constant / xmin, constant / xmax], color="#718096", alpha=0.35, linewidth=0.5, linestyle="--", zorder=0)


def main() -> None:
    corrected = read_rows(CORRECTED)
    old = read_rows(OLD)
    figure, axes = plt.subplots(1, 2, figsize=(8.4, 3.5), sharey=True)
    plot_panel(axes[0], corrected, True)
    plot_panel(axes[1], old, False)
    axes[0].set_title("Corrected polarization grid")
    axes[1].set_title("Original data")
    axes[0].set_ylabel("Polarization overhead (s)")
    axes[0].set_xlabel("n. cores")
    axes[1].set_xlabel("n. cores")
    handles = [
        plt.Line2D([], [], color=color, marker="o", linestyle="", markeredgecolor="black", label=functional)
        for functional, color in COLORS.items()
    ] + [
        plt.Line2D([], [], color="black", marker=marker, linestyle="", label=supercell)
        for supercell, marker in MARKERS.items()
    ]
    figure.legend(handles=handles, loc="upper left", bbox_to_anchor=(0.81, 0.96), frameon=True)
    figure.subplots_adjust(left=0.10, right=0.79, bottom=0.17, top=0.87, wspace=0.18)
    figure.savefig(OUTPUT, bbox_inches="tight")
    print(f"Wrote {OUTPUT}")


if __name__ == "__main__":
    main()
