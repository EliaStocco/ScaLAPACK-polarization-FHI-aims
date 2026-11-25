#!/usr/bin/env python3
"""Plot the Figure 5 polarization-component timing comparison."""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np
import pandas as pd


HERE = Path(__file__).resolve().parent
STYLE_FILE = HERE.parents[1] / "style.mplstyle"
DATA_FILE = HERE / "component_timing_data.csv"
OUTPUT_FILE = HERE / "Figure-5-components.pdf"

COMPONENTS = (
    ("fourier_interpolation_time_s", "Fourier interpolation", "#E69F00", "--", "^"),
    ("dipole_matrix_time_s", "dipole matrix", "#009E73", "--", "D"),
    ("dipole_term_time_s", "dipole term", "#D55E00", "--", "v"),
    ("berry_term_time_s", "Berry term", "#CC79A7", "--", "P"),
)
METHOD_LABELS = {"LAPACK": r"\texttt{LAPACK}", "ScaLAPACK": r"\texttt{ScaLAPACK}"}


def draw_method_panel(axis, data: pd.DataFrame, method: str) -> None:
    subset = data[data["method"] == method].sort_values("ncores")
    handles = []
    for column, label, color, linestyle, marker in COMPONENTS:
        line, = axis.plot(
            subset["ncores"],
            subset[column],
            color=color,
            linestyle=linestyle,
            linewidth=1.1,
            alpha=0.75,
            zorder=2,
        )
        points = axis.scatter(
            subset["ncores"],
            subset[column],
            color=color,
            marker=marker,
            s=20,
            zorder=3,
            label=label,
        )
        handles.append((line, points))
    axis.text(
        0.04,
        0.06,
        METHOD_LABELS[method],
        transform=axis.transAxes,
        ha="left",
        va="bottom",
        bbox={"boxstyle": "round,pad=0.25", "facecolor": "white", "edgecolor": "black", "alpha": 1.0},
        zorder=4,
    )
    axis.set_xscale("log", base=2)
    axis.set_yscale("log")
    axis.set_xlim(7, 1200)
    axis.set_ylim(0.6, 1200)
    axis.set_xticks((8, 16, 32, 64, 128, 256, 512, 1024))
    axis.xaxis.set_major_formatter(mticker.ScalarFormatter())
    axis.yaxis.set_major_locator(mticker.FixedLocator((1, 10, 100, 1000)))
    axis.yaxis.set_major_formatter(mticker.ScalarFormatter())
    axis.grid(axis="y", which="major", color="0.85", linewidth=0.6)
    axis.legend(
        loc="upper left",
        bbox_to_anchor=(1.02, 1.0),
        borderaxespad=0.0,
        framealpha=1.0,
    )


def main() -> None:
    plt.style.use(STYLE_FILE)
    data = pd.read_csv(DATA_FILE)
    figure, axis = plt.subplots(figsize=(5.5, 2.3))
    draw_method_panel(axis, data, "LAPACK")
    axis.set_xlabel("n. cores")
    axis.set_ylabel("CPU time (s)")
    figure.subplots_adjust(left=0.15, right=0.64, bottom=0.22, top=0.96)
    figure.savefig(OUTPUT_FILE)
    print(f"Wrote {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
