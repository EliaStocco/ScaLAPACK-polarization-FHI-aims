#!/usr/bin/env python3
"""Plot timing-component scaling for Figure 7 left- and right-panel series."""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.ticker import FixedLocator, NullFormatter, ScalarFormatter


HERE = Path(__file__).resolve().parent
ROOT = HERE
DATA_FILE = HERE / "figure7_component_data.csv"
DENSE_DATA_FILE = HERE / "reference_dense_component_data.csv"
OUTPUT_FILE = HERE / "Figure-7-components.pdf"
STYLE_FILE = HERE.parent / "style.mplstyle"

SERIES = (
    "4x4x4_lda_corrected",
    "4x4x4_hse06_corrected",
    "8x8x8_lda_corrected",
    "8x8x8_hse06_corrected",
)
DENSE_SERIES = ("4x4x4_lda_dense", "8x8x8_lda_dense")
PLOT_SERIES = (
    "4x4x4_lda_corrected", "4x4x4_hse06_corrected", "4x4x4_lda_dense",
    "8x8x8_lda_corrected", "8x8x8_hse06_corrected", "8x8x8_lda_dense",
)
SERIES_LABELS = {
    "4x4x4_lda_corrected": "4x4x4, LDA",
    "4x4x4_hse06_corrected": "4x4x4, HSE06",
    "8x8x8_lda_corrected": "8x8x8, LDA",
    "8x8x8_hse06_corrected": "8x8x8, HSE06",
    "4x4x4_lda_dense": "4x4x4, LDA (dense)",
    "8x8x8_lda_dense": "8x8x8, LDA (dense)",
}

# Okabe--Ito-inspired colours: distinct in print and readable for common
# forms of colour-vision deficiency.
COMPONENTS = (
    ("polarization_time_s", "Polarization (total)", "#0072B2", "-", "o"),
    ("fourier_interpolation_time_s", "Fourier interpolation", "#E69F00", "--", "^"),
    ("dipole_matrix_time_s", "Dipole matrix", "#009E73", "--", "D"),
    ("dipole_term_time_s", "Dipole term", "#D55E00", "--", "v"),
    ("berry_term_time_s", "Berry term", "#CC79A7", "--", "P"),
)
IDEAL_LINE_COUNT = 10
IDEAL_LINE_STYLE = {
    "color": "#718096",  # pale navy
    "alpha": 0.55,
    "linewidth": 0.6,
    "linestyle": "--",
    "zorder": 0,
}
TIME_TICKS_SECONDS = (1.0, 60.0, 3600.0)
TIME_TICK_LABELS = ("1s", "1m", "1h")
TIME_MINOR_TICKS_SECONDS = tuple(
    tick
    for lower, upper in zip(TIME_TICKS_SECONDS[:-1], TIME_TICKS_SECONDS[1:])
    for tick in np.geomspace(lower, upper, 7)[1:-1]
)
PANEL_ANNOTATION_STYLE = {
    "boxstyle": "round,pad=0.3",
    "facecolor": "white",
    "edgecolor": "black",
    "alpha": 1.0,
}


def add_ideal_scalability_lines(axis, count=IDEAL_LINE_COUNT):
    """Draw pale-navy 1/x guides using the current axis limits."""

    xmin, xmax = sorted(axis.get_xlim())
    ymin, ymax = sorted(axis.get_ylim())
    constants = np.logspace(np.log10(xmin * ymin), np.log10(xmax * ymax), count)
    x = np.logspace(np.log10(xmin), np.log10(xmax), 2)
    for constant in constants:
        axis.plot(x, constant / x, **IDEAL_LINE_STYLE)
    axis.set_xlim(xmin, xmax)
    axis.set_ylim(ymin, ymax)
def plot(
    output: Path = OUTPUT_FILE,
    *,
    show_grid: bool = True,
    show_ideal: bool = True,
) -> None:
    """Create and save the six-panel component-scaling plot."""

    if STYLE_FILE.exists():
        plt.style.use(STYLE_FILE)

    data = pd.read_csv(DATA_FILE)
    selected = data[data["series_id"].isin(SERIES)].copy()
    missing = set(SERIES) - set(selected["series_id"])
    if missing:
        raise ValueError(f"Missing Figure 7 series: {sorted(missing)}")

    dense = pd.read_csv(DENSE_DATA_FILE)
    timing_series = {
        series_id: selected[selected["series_id"] == series_id].sort_values("cores")
        for series_id in SERIES
    }
    timing_series["4x4x4_lda_dense"] = dense[dense["series_id"] == "4x4x4_lda_dense"]
    timing_series["8x8x8_lda_dense"] = dense[dense["series_id"] == "8x8x8_lda_dense"]
    all_values = np.concatenate(
        [
            selected[[column for column, *_ in COMPONENTS]].to_numpy(dtype=float).ravel(),
            dense["polarization_time_s"].to_numpy(dtype=float),
        ]
    )
    shared_ylim = (
        np.nanmin(all_values[all_values > 0]) * 0.8,
        np.nanmax(all_values[all_values > 0]) * 1.25,
    )
    # Match the manuscript's approximately 7-inch full-width figure so that
    # the 10 pt plotting text is not scaled down when LaTeX includes the PDF.
    figure, axes = plt.subplots(2, 3, figsize=(7.5, 4.0), sharex=True, sharey=True)
    axes = axes.ravel()
    handles = []
    labels = []

    for panel_index, (axis, series_id) in enumerate(zip(axes, PLOT_SERIES)):
        subset = timing_series[series_id]
        x = subset["cores"].to_numpy(dtype=float)
        for column, label, color, linestyle, marker in COMPONENTS:
            if column not in subset:
                continue
            y = subset[column].to_numpy(dtype=float)
            valid = np.isfinite(y) & (y > 0)
            scatter = axis.scatter(
                x,
                y,
                color=color,
                marker=marker,
                label=label,
                zorder=3,
            )
            if valid.sum() >= 2:
                fit_slope, fit_intercept = np.polyfit(
                    np.log(x[valid]), np.log(y[valid]), 1
                )
                fit_x = np.geomspace(x[valid].min(), x[valid].max(), 200)
                fit_y = np.exp(fit_intercept) * fit_x**fit_slope
                axis.plot(
                    fit_x,
                    fit_y,
                    color=color,
                    linestyle="-" if column == "polarization_time_s" else "--",
                    linewidth=1.0,
                    alpha=0.65,
                    label="_nolegend_",
                )
            if series_id == SERIES[0]:
                handles.append(scatter)
                labels.append(label)

        title = SERIES_LABELS[series_id]
        # Keep the panel identifier inside the plotting area, using the same
        # white/black framed styling as the shared legend.
        axis.text(
            0.04,
            0.94 if panel_index < 3 else 0.04,
            title,
            transform=axis.transAxes,
            ha="left",
            va="top" if panel_index < 3 else "bottom",
            bbox=PANEL_ANNOTATION_STYLE,
            zorder=5,
        )
        axis.set_xscale("log", base=2)
        axis.set_yscale("log")
        axis.set_xlim(110, 2300)
        axis.set_ylim(*shared_ylim)
        axis.set_yticks(TIME_TICKS_SECONDS, labels=TIME_TICK_LABELS)
        axis.yaxis.set_minor_locator(FixedLocator(TIME_MINOR_TICKS_SECONDS))
        axis.yaxis.set_minor_formatter(NullFormatter())
        if show_ideal:
            add_ideal_scalability_lines(axis)
        axis.set_xticks((128, 256, 512, 1024, 2048))
        axis.get_xaxis().set_major_formatter(ScalarFormatter())
        if show_grid:
            axis.grid(axis="y", which="major", color="0.75", linewidth=0.6)
            axis.grid(axis="y", which="minor", color="0.88", linewidth=0.4)

    axes[3].set_xlabel("n. cores")
    axes[4].set_xlabel("n. cores")
    axes[5].set_xlabel("n. cores")
    axes[0].set_ylabel("CPU time")
    axes[3].set_ylabel("CPU time")
    figure.subplots_adjust(left=0.07, right=0.70, bottom=0.13, top=0.89,
                           wspace=0.12, hspace=0.22)
    axes[2].legend(
        handles,
        labels,
        loc="upper left",
        frameon=True,
        ncol=1,
        bbox_to_anchor=(1.02, 1.0),
        borderaxespad=0,
        facecolor="white",
        edgecolor="black",
        framealpha=1.0,
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(output)
    plt.close(figure)
    print(f"Wrote {output}")


if __name__ == "__main__":
    plot()
    plot(
        ROOT / "Figure-7-components-grid.pdf",
        show_ideal=False,
    )
    plot(
        ROOT / "Figure-7-components-ideal.pdf",
        show_grid=False,
    )
