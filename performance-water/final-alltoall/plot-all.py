#!/usr/bin/env python3
"""Create one scaling plot containing every functional and water-box series."""

from __future__ import annotations

import csv
import json
from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.image as mpimg
import numpy as np
from matplotlib.lines import Line2D
from matplotlib.offsetbox import AnnotationBbox, OffsetImage
from matplotlib.ticker import FixedLocator, NullLocator, ScalarFormatter


HERE = Path(__file__).resolve().parent
STYLE = HERE.parents[1] / "style.mplstyle"
FUNCTIONALS = ["revPBE", "revPBE0"]
FUNCTIONAL_COLORS = {"revPBE": "#1f77b4", "revPBE0": "#ff7f0e"}
MOLECULES = [128, 196]
MARKERS = {"revPBE": "x", "revPBE0": "+"}
LINESTYLES = {128: "-.", 196: "--"}
XTICKS = [128, 256, 512, 1024, 2048]


def add_inverse_lines(axis: plt.Axes, count: int = 18) -> None:
    """Draw log-spaced guides for ideal inverse-core-count scaling."""

    xmin, xmax = axis.get_xlim()
    ymin, ymax = axis.get_ylim()
    constants = np.logspace(np.log10(xmin * ymin), np.log10(xmax * ymax), count)
    x = np.array([xmin, xmax])
    for constant in constants:
        axis.plot(x, constant / x, color="0.65", alpha=0.4, linewidth=0.45, ls="--", zorder=0)
    axis.set_xlim(xmin, xmax)
    axis.set_ylim(ymin, ymax)


def power_law_angle(axis: plt.Axes, exponent: float) -> float:
    """Return the on-page angle of ``y ∝ x**exponent`` for this axis."""

    xmin, xmax = axis.get_xlim()
    ymin, ymax = axis.get_ylim()
    x = np.sqrt(xmin * xmax)
    y = np.sqrt(ymin * ymax)
    scale = 1.1
    start, end = axis.transData.transform(((x, y), (x * scale, y * scale**exponent)))
    return np.degrees(np.arctan2(end[1] - start[1], end[0] - start[0]))


def add_water_box_image(
    axis: plt.Axes, image_path: Path, position: tuple[float, float], zoom: float
) -> None:
    """Place a water-box rendering using axes-fraction coordinates."""

    image = mpimg.imread(image_path)
    axis.add_artist(
        AnnotationBbox(
            OffsetImage(image, zoom=zoom),
            position,
            xycoords="axes fraction",
            frameon=False,
        )
    )


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
        fits = json.load(handle)["linear"]

    fig, axis = plt.subplots(figsize=(6,4))
    for functional in FUNCTIONALS:
        for molecules in MOLECULES:
            subset = sorted(
                (
                    row
                    for row in data
                    if row["functional"] == functional and row["molecules"] == molecules
                ),
                key=lambda row: row["ncores"],
            )
            if not subset:
                continue

            color = FUNCTIONAL_COLORS[functional]
            axis.scatter(
                [row["ncores"] for row in subset],
                [row["polarization_time_s"] for row in subset],
                color=color,
                marker=MARKERS[functional],
                linewidths=1.6,
                zorder=3,
            )
            parameters = fits[functional][str(molecules)]
            x = np.logspace(np.log10(subset[0]["ncores"]), np.log10(subset[-1]["ncores"]), 300)
            axis.plot(
                x,
                parameters["A"] * x**parameters["m"],
                color=color,
                ls=LINESTYLES[molecules],
                alpha=0.8,
            )

    axis.set_xscale("log")
    axis.set_yscale("log")
    axis.set_xlabel("n. cores")
    axis.set_ylabel("CPU time (s)")
    # axis.set_title("Liquid water polarization scaling")
    axis.xaxis.set_major_locator(FixedLocator(XTICKS))
    axis.xaxis.set_major_formatter(ScalarFormatter())
    axis.xaxis.set_minor_locator(NullLocator())
    add_inverse_lines(axis)

    add_water_box_image(axis, HERE / "water.m=128.png", (0.10, 0.78), 0.035)
    add_water_box_image(axis, HERE / "water.m=196.png", (0.89, 0.78), 0.045)

    axis.legend(
        handles=[
            Line2D(
                [0],
                [0],
                color=FUNCTIONAL_COLORS[functional],
                marker=MARKERS[functional],
                ls="-",
                markeredgewidth=1.4,
                label=functional,
            )
            for functional in FUNCTIONALS
        ],
        title="functional",
        loc="lower center",
        bbox_to_anchor=(0.5, 1.02),
        ncol=2,
    )

    annotation_positions = {
        ("revPBE", 128): (0.78, 0.15),
        ("revPBE0", 128): (0.37, 0.29),
        ("revPBE", 196): (0.35, 0.69),
        ("revPBE0", 196): (0.62, 0.56),
    }
    annotations = []
    for (functional, molecules), (xpos, ypos) in annotation_positions.items():
        exponent = fits[functional][str(molecules)]["m"]
        annotation = axis.text(
            xpos,
            ypos,
            f"$m={exponent:.2f}$",
            color=FUNCTIONAL_COLORS[functional],
            transform=axis.transAxes,
            ha="center",
            va="center",
        )
        annotations.append((annotation, exponent))

    fig.tight_layout()
    fig.canvas.draw()
    for annotation, exponent in annotations:
        annotation.set_rotation(power_law_angle(axis, exponent))
    output = HERE / "water-all.pdf"
    fig.savefig(output, bbox_inches="tight")
    print(f"Wrote {output}")


if __name__ == "__main__":
    main()
