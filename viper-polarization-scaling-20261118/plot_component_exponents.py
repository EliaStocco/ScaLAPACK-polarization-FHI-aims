#!/usr/bin/env python3
"""Plot log--log scalability exponents for the Figure 7 timing components.

The plotted coefficient is the positive ``m`` in ``time = A * cores**(-m)``.
Error bars are one-standard-error uncertainties of the fitted log--log slope.
The second panel shows average measured component cost shares.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


HERE = Path(__file__).resolve().parent
ROOT = HERE
DATA_FILE = HERE / "figure7_component_data.csv"
DENSE_DATA_FILE = HERE / "reference_dense_component_data.csv"
STYLE_FILE = HERE.parent / "style.mplstyle"
DEFAULT_OUTPUT = HERE / "Figure-7-component-exponents.pdf"

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
COMPONENTS = (
    ("polarization_time_s", "Polarization (total)", "#0072B2"),
    ("fourier_interpolation_time_s", "Fourier interpolation", "#E69F00"),
    ("dipole_matrix_time_s", "Dipole matrix", "#009E73"),
    ("dipole_term_time_s", "Dipole term", "#D55E00"),
    ("berry_term_time_s", "Berry term", "#CC79A7"),
)
# Keep the component legend order identical to the component-scaling plots.
SHARE_COMPONENTS = COMPONENTS[1:]


def fit_loglog(cores: np.ndarray, values: np.ndarray) -> tuple[float, float, float] | None:
    """Return positive ``m``, its 1-sigma error, and fitted prefactor."""

    valid = np.isfinite(cores) & np.isfinite(values) & (cores > 0) & (values > 0)
    if valid.sum() < 3:
        return None
    log_cores = np.log(cores[valid])
    log_values = np.log(values[valid])
    slope, intercept = np.polyfit(log_cores, log_values, 1)
    residuals = log_values - (intercept + slope * log_cores)
    degrees_of_freedom = len(log_cores) - 2
    if degrees_of_freedom <= 0:
        return -float(slope), float("nan"), float(np.exp(intercept))
    slope_error = np.sqrt(
        np.sum(residuals**2) / degrees_of_freedom
        / np.sum((log_cores - log_cores.mean()) ** 2)
    )
    return -float(slope), float(slope_error), float(np.exp(intercept))


def plot(output: Path = DEFAULT_OUTPUT) -> None:
    """Create and save the grouped component-exponent bar plot."""

    if STYLE_FILE.exists():
        plt.style.use(STYLE_FILE)
    data = pd.read_csv(DATA_FILE)
    selected = data[data["series_id"].isin(SERIES)].copy()
    if set(selected["series_id"]) != set(SERIES):
        raise ValueError("The timing data do not contain all Figure 7 series")

    dense = pd.read_csv(DENSE_DATA_FILE)
    timing_series = {
        series_id: selected[selected["series_id"] == series_id].sort_values("cores")
        for series_id in SERIES
    }
    timing_series["4x4x4_lda_dense"] = dense[dense["series_id"] == "4x4x4_lda_dense"]
    timing_series["8x8x8_lda_dense"] = dense[dense["series_id"] == "8x8x8_lda_dense"]

    fig = plt.figure(figsize=(11.0, 5.0))
    layout = fig.add_gridspec(
        1, 2, width_ratios=(1.0, 1.65), wspace=0.35,
        left=0.08, right=0.82, bottom=0.20, top=0.94,
    )
    ax = fig.add_subplot(layout[0, 0])
    share_layout = layout[0, 1].subgridspec(2, 3, wspace=0.12, hspace=0.18)
    share_axes = [fig.add_subplot(share_layout[row, col])
                  for row in range(2) for col in range(3)]
    x = np.arange(len(PLOT_SERIES), dtype=float)
    width = 0.15
    exponent_handles = []
    for component_index, (column, label, color) in enumerate(COMPONENTS):
        values = []
        errors = []
        for series_id in PLOT_SERIES:
            subset = timing_series[series_id]
            if column not in subset:
                fit = None
            else:
                fit = fit_loglog(
                    subset["cores"].to_numpy(float), subset[column].to_numpy(float)
                )
            values.append(np.nan if fit is None else fit[0])
            errors.append(0.0 if fit is None else fit[1])
        offset = (component_index - (len(COMPONENTS) - 1) / 2) * width
        bars = ax.bar(
            x + offset,
            values,
            width,
            yerr=errors,
            capsize=3,
            color=color,
            edgecolor="black",
            linewidth=0.45,
            label=label,
            error_kw={"elinewidth": 0.8, "capthick": 0.8},
        )
        exponent_handles.append(bars)

    labels = [
        "4×4×4\nLDA", "4×4×4\nHSE06", "4×4×4\nLDA (dense)",
        "8×8×8\nLDA", "8×8×8\nHSE06", "8×8×8\nLDA (dense)",
    ]
    ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=30, ha="right")
    ax.set_ylabel(r"Scalability exponent $m$")
    ax.set_ylim(0.0, 1.45)
    ax.grid(axis="y", linestyle="--", linewidth=0.5, alpha=0.35)

    # Show measured component costs as normalized, stacked rectangles.  The
    # total bar is deliberately omitted: the four component values are
    # normalized independently at each measured core count.
    share_handles = []
    for series_index, (series_id, share_ax) in enumerate(zip(PLOT_SERIES, share_axes)):
        subset = timing_series[series_id]
        cores = subset["cores"].to_numpy(float)
        tile_positions = np.arange(len(cores), dtype=float)
        component_values = subset[[column for column, _, _ in SHARE_COMPONENTS]].to_numpy(float)
        component_values[~np.isfinite(component_values)] = 0.0
        component_values = np.maximum(component_values, 0.0)
        totals = component_values.sum(axis=1)
        shares_matrix = np.divide(
            100.0 * component_values,
            totals[:, None],
            out=np.zeros_like(component_values),
            where=totals[:, None] != 0,
        )
        bottoms = np.zeros(len(cores))
        for component_index, (_, label, color) in enumerate(SHARE_COMPONENTS):
            bars = share_ax.bar(
                tile_positions,
                shares_matrix[:, component_index],
                width=1.0,
                bottom=bottoms,
                color=color,
                edgecolor="black",
                linewidth=0.45,
                label=label,
            )
            if series_index == 0:
                share_handles.append(bars)
            bottoms += shares_matrix[:, component_index]
        share_ax.set_xlim(-0.5, len(cores) - 0.5)
        share_ax.set_xticks(tile_positions)
        share_ax.set_xticklabels([str(int(core)) for core in cores])
        share_ax.set_ylim(0.0, 100.0)
        share_ax.set_yticks((0, 25, 50, 75, 100))
        share_ax.grid(axis="y", linestyle="--", linewidth=0.5, alpha=0.35)
        share_ax.set_title(labels[series_index].replace("\n", ", "))
        if series_index % 3 == 0:
            share_ax.set_ylabel(r"Cost share (\%)")
        else:
            share_ax.set_yticklabels([])
        if series_index < 3:
            share_ax.set_xticklabels([])

    fig.legend(
        exponent_handles,
        [label for _, label, _ in COMPONENTS],
        loc="upper left",
        bbox_to_anchor=(0.80, 0.94),
        borderaxespad=0,
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output)
    plt.close(fig)
    print(f"Wrote {output}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    plot(args.output)


if __name__ == "__main__":
    from plot_component_exponents_split import main as split_main

    split_main()
