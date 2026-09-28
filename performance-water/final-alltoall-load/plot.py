#!/usr/bin/env python3
"""Plot polarization overhead scaling for all functionals and water boxes."""

from __future__ import annotations

import json
import csv
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.ticker import FixedLocator, NullLocator, ScalarFormatter


HERE = Path(__file__).resolve().parent
STYLE = HERE.parents[1] / "style.mplstyle"
FUNCTIONALS = ["revPBE", "revPBE0", "HSE06"]
MOLECULES = [128, 196]
MARKERS = {128: "o", 196: "s"}
COLORS = {128: "#1f77b4", 196: "#ff7f0e"}
XTICKS = [128, 256, 512, 1024, 2048]
XLIM = (110, 2400)


def add_inverse_lines(axis: plt.Axes, count: int = 14) -> None:
    """Draw log-spaced guides for ideal inverse-core-count scaling."""

    xmin, xmax = axis.get_xlim()
    ymin, ymax = axis.get_ylim()
    constants = np.logspace(np.log10(xmin * ymin), np.log10(xmax * ymax), count)
    x = np.array([xmin, xmax])
    for constant in constants:
        axis.plot(x, constant / x, color="0.65", alpha=0.45, linewidth=0.45, ls="--", zorder=0)
    axis.set_xlim(xmin, xmax)
    axis.set_ylim(ymin, ymax)


def format_exponent(exponent: float) -> str:
    return f"$m={exponent:.2f}$"


def main() -> None:
    if STYLE.exists():
        plt.style.use(STYLE)

    with (HERE / "analysis-dataframe.csv").open(newline="") as handle:
        data = [
            {
                "functional": row["functional"],
                "molecules": int(row["molecules"]),
                "ncores": int(row["ncores"]),
                "polarization_time_s": float(row["polarization_time_s"]),
            }
            for row in csv.DictReader(handle)
        ]
    with (HERE / "fit.json").open() as handle:
        fit = json.load(handle)["linear"]

    fig, axes = plt.subplots(
        1, len(FUNCTIONALS), figsize=(9.6, 3.5), sharex=True, sharey=True
    )

    for axis, functional in zip(axes, FUNCTIONALS):
        functional_data = [row for row in data if row["functional"] == functional]
        if not functional_data:
            axis.set_visible(False)
            continue

        for molecules in MOLECULES:
            subset = sorted(
                (row for row in functional_data if row["molecules"] == molecules),
                key=lambda row: row["ncores"],
            )
            if not subset:
                continue

            color = COLORS[molecules]
            axis.scatter(
                [row["ncores"] for row in subset],
                [row["polarization_time_s"] for row in subset],
                marker=MARKERS[molecules],
                color=color,
                label=f"{molecules} molecules",
                zorder=3,
            )

            parameters = fit[functional][str(molecules)]
            x = np.logspace(
                np.log10(subset[0]["ncores"]),
                np.log10(subset[-1]["ncores"]),
                300,
            )
            axis.plot(x, parameters["A"] * x**parameters["m"], color=color, ls="--", alpha=0.8)
            axis.text(
                0.97,
                0.18 if molecules == 128 else 0.31,
                format_exponent(parameters["m"]),
                color=color,
                ha="right",
                transform=axis.transAxes,
            )

        axis.set_title(functional)
        axis.set_xscale("log")
        axis.set_yscale("log")
        axis.set_xlim(*XLIM)
        axis.set_xlabel("n. cores")
        axis.xaxis.set_major_locator(FixedLocator(XTICKS))
        axis.xaxis.set_major_formatter(ScalarFormatter())
        axis.xaxis.set_minor_locator(NullLocator())
        add_inverse_lines(axis)

    axes[0].set_ylabel("polarization overhead (s)")
    axes[0].legend(title="water box", loc="lower left")
    fig.suptitle("Liquid water polarization scaling")
    fig.tight_layout()
    fig.savefig(HERE / "water.pdf", bbox_inches="tight")
    print(f"Wrote {HERE / 'water.pdf'}")


if __name__ == "__main__":
    main()
