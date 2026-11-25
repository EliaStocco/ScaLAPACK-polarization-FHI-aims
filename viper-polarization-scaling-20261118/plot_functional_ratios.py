#!/usr/bin/env python3
"""Compare the HSE06 and LDA polarization-timing contributions."""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.ticker import ScalarFormatter


HERE = Path(__file__).resolve().parent
DATA_FILE = HERE / "figure7_component_data.csv"
OUTPUT_FILE = HERE / "Figure-S3-functional-ratios.pdf"
STYLE_FILE = HERE.parent / "style.mplstyle"

SUPERCELLS = ("4x4x4", "8x8x8")
SUPERCELL_TITLES = {
    "4x4x4": r"$4\!\times\!4\!\times\!4$",
    "8x8x8": r"$8\!\times\!8\!\times\!8$",
}
COMPONENTS = (
    ("polarization_time_s", "Net polarization time", "black", "o", "-"),
    ("fourier_interpolation_time_s", "Fourier interpolation", "#E69F00", "^", "--"),
    ("dipole_matrix_time_s", "Dipole matrix", "#009E73", "D", "--"),
    ("dipole_term_time_s", "Dipole term", "#D55E00", "v", "--"),
    ("berry_term_time_s", "Berry term", "#CC79A7", "P", "--"),
)


def timing_ratios(data: pd.DataFrame, supercell: str) -> pd.DataFrame:
    """Return component-wise HSE06/LDA ratios at shared core counts."""

    subset = data[data["series_id"].str.startswith(f"{supercell}_")]
    lda = subset[subset["series_id"] == f"{supercell}_lda_corrected"]
    hse = subset[subset["series_id"] == f"{supercell}_hse06_corrected"]
    columns = ["cores", *[column for column, *_ in COMPONENTS]]
    return hse[columns].merge(lda[columns], on="cores", suffixes=("_hse", "_lda"))


def plot(output: Path = OUTPUT_FILE) -> None:
    """Create a two-panel comparison of HSE06 and LDA timer contributions."""

    if STYLE_FILE.exists():
        plt.style.use(STYLE_FILE)
    # Reserve a dedicated column for the external legend; the shared style
    # otherwise enables automatic layout, which would expand the axes beneath it.
    plt.rcParams["figure.autolayout"] = False

    data = pd.read_csv(DATA_FILE)
    figure, axes = plt.subplots(1, 2, figsize=(7.5, 2.45), sharex=True, sharey=True)
    handles = []

    for axis, supercell in zip(axes, SUPERCELLS):
        ratios = timing_ratios(data, supercell).sort_values("cores")
        cores = ratios["cores"]
        for column, label, color, marker, linestyle in COMPONENTS:
            (line,) = axis.plot(
                cores,
                ratios[f"{column}_hse"] / ratios[f"{column}_lda"],
                color=color,
                marker=marker,
                linestyle=linestyle,
                linewidth=1.25,
                markersize=5.5,
                label=label,
            )
            if supercell == SUPERCELLS[0]:
                handles.append(line)

        axis.axhline(1.0, color="0.40", linewidth=0.8, zorder=0)
        axis.set_xscale("log", base=2)
        axis.set_xlim(110, 2300)
        axis.set_xticks((128, 256, 512, 1024, 2048))
        axis.xaxis.set_major_formatter(ScalarFormatter())
        axis.text(
            0.5,
            1.04,
            SUPERCELL_TITLES[supercell],
            ha="center",
            va="bottom",
            transform=axis.transAxes,
            bbox={"facecolor": "white", "edgecolor": "none", "pad": 1.0},
        )
        axis.set_xlabel("n. cores")

    axes[0].set_ylabel(r"Timing ratio, $t_{\mathrm{HSE06}}/t_{\mathrm{LDA}}$")
    axes[0].set_ylim(0.5, 2.0)
    axes[0].set_yticks((0.5, 0.75, 1.0, 1.25, 1.5, 1.75, 2.0))
    figure.subplots_adjust(left=0.10, right=0.63, bottom=0.25, top=0.88, wspace=0.18)
    figure.legend(
        handles=handles,
        loc="upper left",
        bbox_to_anchor=(0.65, 0.88),
        borderaxespad=0,
        frameon=True,
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
