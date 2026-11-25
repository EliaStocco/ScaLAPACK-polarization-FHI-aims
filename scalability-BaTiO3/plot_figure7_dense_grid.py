#!/usr/bin/env python3
"""Create the dense-$k$-grid BaTiO3 core-scalability plot for the SI."""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.ticker import FixedLocator, NullLocator, ScalarFormatter
import numpy as np
import pandas as pd

from plot_figure7_left_only import (
    CORE_TICKS,
    FIT_LINE_STYLE,
    INVERSE_GUIDE_LINE_COUNT,
    INVERSE_GUIDE_LINE_STYLE,
    LDA_COLOR,
    REFERENCE_DATAFRAME,
    REFERENCE_FIT,
    STYLE_FILE,
    X_MARGIN_FACTOR,
    add_inverse_lines,
    add_line_relative_annotation,
    power_law_angle,
)


ROOT = Path(__file__).resolve().parent
OUTPUT_PDF = ROOT / "Figure-S4-dense-k-grid-scalability.pdf"
FIGSIZE = (7.5, 2.35)
SUPERCELLS = (
    (4, r"$4\!\times\!4\!\times\!4$", (130, 2000), 0.60, -10),
    (8, r"$8\!\times\!8\!\times\!8$", (3000, 14000), 0.72, -10),
)


def main() -> None:
    """Plot each dense-grid supercell in a compact, independently scaled panel."""

    plt.style.use(STYLE_FILE)
    plt.rcParams.update({"figure.autolayout": False})

    dataframe = pd.read_csv(REFERENCE_DATAFRAME)
    dataframe = dataframe.pivot(
        index=["supercell", "ncores"], columns="calculation", values="time"
    ).reset_index()
    dataframe = dataframe.dropna(subset=["dipole", "scf"])
    dataframe["time"] = dataframe["dipole"] - dataframe["scf"]
    with REFERENCE_FIT.open() as file:
        fit = json.load(file)["linear"]

    figure, axes = plt.subplots(1, 2, figsize=FIGSIZE, sharex=True)
    annotations = []
    for axis, (supercell, title, ylim, fraction, offset) in zip(axes, SUPERCELLS):
        subset = dataframe[dataframe["supercell"] == supercell].sort_values("ncores")
        parameters = fit[str(supercell)]
        x = np.logspace(
            np.log10(subset["ncores"].min()), np.log10(subset["ncores"].max()), 400
        )
        axis.scatter(subset["ncores"], subset["time"], color=LDA_COLOR)
        axis.plot(
            x,
            parameters["A"] * x**parameters["m"],
            color=LDA_COLOR,
            linestyle=FIT_LINE_STYLE,
            alpha=0.65,
        )
        axis.set_xscale("log")
        axis.set_yscale("log")
        axis.set_xlim(min(CORE_TICKS) / X_MARGIN_FACTOR, max(CORE_TICKS) * X_MARGIN_FACTOR)
        axis.set_ylim(*ylim)
        axis.xaxis.set_major_locator(FixedLocator(CORE_TICKS))
        axis.xaxis.set_major_formatter(ScalarFormatter())
        axis.xaxis.set_minor_locator(NullLocator())
        axis.yaxis.set_minor_locator(NullLocator())
        axis.set_xlabel("n. cores")
        axis.set_title(title)
        add_inverse_lines(axis, INVERSE_GUIDE_LINE_COUNT, **INVERSE_GUIDE_LINE_STYLE)
        if supercell == 4:
            annotations.append(
                add_line_relative_annotation(
                    axis,
                    parameters["A"],
                    parameters["m"],
                    rf"$m={abs(parameters['m']):.2f}$",
                    LDA_COLOR,
                    fraction,
                    offset,
                )
            )
        else:
            annotation = axis.text(
                0.72,
                0.28,
                rf"$m={abs(parameters['m']):.2f}$",
                color=LDA_COLOR,
                transform=axis.transAxes,
                ha="center",
                va="center",
            )
            annotations.append((axis, annotation, parameters["m"]))

    annotations.append(
        add_line_relative_annotation(
            axes[0],
            None,
            -1,
            r"ideal scalability: $m=1$",
            "gray",
            0.53,
            10,
        )
    )
    axes[0].set_ylabel("CPU time (s)")
    figure.subplots_adjust(left=0.095, right=0.99, bottom=0.25, top=0.87, wspace=0.20)
    figure.canvas.draw()
    for axis, annotation, exponent in annotations:
        annotation.set_rotation(power_law_angle(axis, exponent))
    figure.savefig(OUTPUT_PDF)
    plt.close(figure)
    print(f"Wrote {OUTPUT_PDF}")


if __name__ == "__main__":
    main()
