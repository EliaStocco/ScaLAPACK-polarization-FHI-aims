#!/usr/bin/env python3
"""Recreate the BaTiO3 and water performance plots in one 6-inch-wide PDF.

Run from any directory with:

    python3 merge-performance-plots-new.py

The output is intended for ``\\includegraphics[width=\\linewidth]{...}``
where ``\\linewidth`` is about 6 inches.  Its plotting text is set to 10 pt.
"""

from pathlib import Path
import json

import matplotlib.image as mpimg
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.offsetbox import AnnotationBbox, OffsetImage
from matplotlib.ticker import FixedLocator, NullLocator, ScalarFormatter
import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parent
OUTPUT_PDF = ROOT / "performance-combined.pdf"

# Keep the overall width at 6 inches.  Adjust only the second value as needed.
FIGSIZE = (8,3)


def add_inverse_lines(ax, n_lines: int, **plot_kwargs) -> None:
    """Add evenly distributed 1/x guide lines within the current axis limits."""

    xmin, xmax = sorted(ax.get_xlim())
    ymin, ymax = sorted(ax.get_ylim())
    constants = np.logspace(np.log10(xmin * ymin), np.log10(xmax * ymax), n_lines)
    x = np.logspace(np.log10(xmin), np.log10(xmax), 2)

    for constant in constants:
        ax.plot(x, constant / x, **plot_kwargs)

    ax.set_xlim(xmin, xmax)
    ax.set_ylim(ymin, ymax)


def add_image(ax, image_path: Path, position: tuple[float, float], zoom: float) -> None:
    image = mpimg.imread(image_path)
    imagebox = OffsetImage(image, zoom=zoom)
    ax.add_artist(
        AnnotationBbox(
            imagebox,
            position,
            xycoords="axes fraction",
            frameon=False,
        )
    )


def add_image_arrow(
    ax,
    tail: tuple[float, float],
    target: tuple[float, float],
) -> None:
    """Connect a structure image to a point on its corresponding curve."""

    ax.annotate(
        "",
        xy=target,
        xycoords="data",
        xytext=tail,
        textcoords="axes fraction",
        arrowprops={
            "arrowstyle": "-|>",
            "color": "gray",
            # A shallow arc keeps the arrow from the left-hand image readable
            # without the pronounced right-angle bend.
            "connectionstyle": "arc3,rad=-0.12",
            "mutation_scale": 8,
            "shrinkA": 4,
            "shrinkB": 2,
        },
        zorder=4,
    )


def add_vertical_image_arrow(
    ax,
    tail: tuple[float, float],
    curves: tuple[tuple[float, float], ...],
) -> None:
    """Draw a vertical arrow from an image to the midpoint of fitted curves."""

    xdata, _ = ax.transData.inverted().transform(ax.transAxes.transform((tail[0], 0.5)))
    ydata = np.mean([amplitude * xdata**exponent for amplitude, exponent in curves])
    _, target_y = ax.transAxes.inverted().transform(ax.transData.transform((xdata, ydata)))
    ax.annotate(
        "",
        xy=(tail[0], target_y),
        xycoords="axes fraction",
        xytext=tail,
        textcoords="axes fraction",
        arrowprops={
            "arrowstyle": "-|>",
            "color": "gray",
            "mutation_scale": 8,
            "shrinkA": 4,
            "shrinkB": 2,
        },
        zorder=4,
    )


def power_law_angle(ax, exponent: float) -> float:
    """Return the on-page angle of ``y ∝ x**exponent`` for *ax*."""

    xmin, xmax = ax.get_xlim()
    ymin, ymax = ax.get_ylim()
    x = np.sqrt(xmin * xmax)
    y = np.sqrt(ymin * ymax)
    scale = 1.1
    start, end = ax.transData.transform(((x, y), (x * scale, y * scale ** exponent)))
    return np.degrees(np.arctan2(end[1] - start[1], end[0] - start[0]))


def add_power_law_annotation(
    ax,
    position: tuple[float, float],
    text: str,
    exponent: float,
    color: str,
) -> tuple:
    """Add an annotation whose rotation is applied once layout is final."""

    annotation = ax.text(
        *position,
        text,
        transform=ax.transAxes,
        ha="center",
        va="center",
        color=color,
    )
    return ax, annotation, exponent


def plot_batio3(ax) -> list[tuple]:
    directory = ROOT / "performance-BaTiO3"
    dataframe = pd.read_csv(directory / "dataframe.csv")
    dataframe = dataframe.pivot(
        index=["supercell", "ncores"], columns="calculation", values="time"
    ).reset_index()
    dataframe = dataframe.dropna(subset=["dipole", "scf"])
    dataframe["time"] = dataframe["dipole"] - dataframe["scf"]

    with (directory / "fit.json").open() as file:
        fit = json.load(file)

    for marker, supercell in zip(("s", "o"), (4, 8)):
        subset = dataframe[dataframe["supercell"] == supercell].copy()
        subset = subset.sort_values("ncores")
        ax.scatter(subset["ncores"], subset["time"], marker=marker, label=f"{supercell}x{supercell}x{supercell}")

        x = np.logspace(np.log10(subset["ncores"].min()), np.log10(subset["ncores"].max()), 1000)
        params = fit["linear"][str(supercell)]
        ax.plot(x, params["A"] * x ** params["m"], linestyle="--", alpha=0.5)

    # Half the original zooms because the panel is half the original width.
    factor = 1.5
    add_image(ax, directory / "BaTiO3.4x4x4.png", (0.1, 0.65), 0.02*factor)
    add_image(ax, directory / "BaTiO3.8x8x8.png", (0.85, 0.6), 0.04*factor)
    annotations = [
        add_power_law_annotation(ax, (0.5, 0.48), r"ideal scalability: $m=1$", -1, "gray"),
        add_power_law_annotation(ax, (0.4, 0.31), r"$m=0.94$", -0.94, "#1f77b4"),
        add_power_law_annotation(ax, (0.85, 0.92), r"$m=0.95$", -0.95, "#ff7f0e"),
    ]

    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlabel("n. cores")
    ax.set_ylabel("CPU time (s)")
    legend = ax.legend(title="supercell:", loc="lower left")
    legend._legend_box.align = "left"
    ax.xaxis.set_major_locator(FixedLocator((128, 256, 512, 1024, 2048)))
    ax.xaxis.set_major_formatter(ScalarFormatter())
    ax.xaxis.set_minor_locator(NullLocator())
    add_inverse_lines(ax, 20, color="gray", alpha=0.5, linewidth=0.5, linestyle="--")
    return annotations


def plot_water(ax) -> list[tuple]:
    directory = ROOT / "performance-water" / "final"
    dataframe = pd.read_csv(directory / "analysis-dataframe.csv")
    functionals = ("revPBE", "revPBE0")
    colors = {"revPBE": "#1f77b4", "revPBE0": "#ff7f0e"}
    markers = {"revPBE": "s", "revPBE0": "o"}
    dataframe = dataframe[dataframe["functional"].isin(functionals)].copy()
    dataframe["time"] = dataframe["polarization_time_s"]

    with (directory / "fit.json").open() as file:
        fit = json.load(file)

    for functional in functionals:
        for molecules in (128, 196):
            subset = dataframe[
                (dataframe["functional"] == functional)
                & (dataframe["molecules"] == molecules)
            ].copy()
            subset = subset.sort_values("ncores")
            ax.scatter(
                subset["ncores"],
                subset["time"],
                marker=markers[functional],
                color=colors[functional],
            )

            x = np.logspace(np.log10(subset["ncores"].min()), np.log10(subset["ncores"].max()), 1000)
            params = fit["linear"][functional][str(molecules)]
            ax.plot(x, params["A"] * x ** params["m"], color=colors[functional], linestyle="--", alpha=0.65)

    factor = 1.5
    add_image(ax, directory / "water.m=128.png", (0.1, 0.67), 0.02*factor)
    add_image(ax, directory / "water.m=196.png", (0.89, 0.67), 0.0275*factor)
    annotations = [
        add_power_law_annotation(
    ax,
    (0.55, 0.75),  # x, y in axes-relative coordinates
    r"ideal scalability: $m=1$",
    -1,
    "gray",
),
        add_power_law_annotation(ax, (0.2, 0.5), rf"$m={abs(fit['linear']['revPBE']['128']['m']):.2f}$", fit["linear"]["revPBE"]["128"]["m"], colors["revPBE"]),
        add_power_law_annotation(ax, (0.85, 0.16), rf"$m={abs(fit['linear']['revPBE0']['128']['m']):.2f}$", fit["linear"]["revPBE0"]["128"]["m"], colors["revPBE0"]),
        add_power_law_annotation(ax, (0.25, 0.8), rf"$m={abs(fit['linear']['revPBE']['196']['m']):.2f}$", fit["linear"]["revPBE"]["196"]["m"], colors["revPBE"]),
        add_power_law_annotation(ax, (0.85, 0.43), rf"$m={abs(fit['linear']['revPBE0']['196']['m']):.2f}$", fit["linear"]["revPBE0"]["196"]["m"], colors["revPBE0"]),
    ]

    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlabel("n. cores")
    ax.set_ylabel("CPU time (s)")
    ax.legend(
        handles=[
            Line2D(
                [0], [0], color=colors[functional], marker=markers[functional],
                linestyle="--", label=functional,
            )
            for functional in functionals
        ],
        title="functional:",
        loc="lower left",
    )
    ax.xaxis.set_major_locator(FixedLocator((128, 256, 512, 1024, 2048)))
    ax.xaxis.set_major_formatter(ScalarFormatter())
    ax.xaxis.set_minor_locator(NullLocator())
    ax.yaxis.set_major_locator(FixedLocator((50, 100, 200, 400)))
    ax.yaxis.set_major_formatter(ScalarFormatter())
    ax.yaxis.set_minor_locator(NullLocator())
    ax.set_ylim(None, 450)
    add_inverse_lines(ax, 20, color="gray", alpha=0.5, linewidth=0.5, linestyle="--")
    arrow_core_count = 384
    small_curve_times = [
        fit["linear"][functional]["128"]["A"]
        * arrow_core_count**fit["linear"][functional]["128"]["m"]
        for functional in functionals
    ]
    #print(np.mean(small_curve_times))
    add_image_arrow(ax, (0.17, 0.67), (arrow_core_count, 65))
    # Keep the right-hand arrow's origin, but point it into the requested
    # 512--1024-core, 100--150-second region.
    add_image_arrow(ax, (0.89, 0.55), (800, 110))
    return annotations


def main() -> None:
    plt.style.use(ROOT / "style.mplstyle")
    plt.rcParams.update(
        {
            "figure.autolayout": False,
        }
    )

    figure, axes = plt.subplots(1, 2, figsize=FIGSIZE)
    annotations = plot_batio3(axes[0]) + plot_water(axes[1])
    figure.subplots_adjust(left=0, right=1, bottom=0, top=1, wspace=0.15)
    plt.tight_layout()
    figure.canvas.draw()
    for ax, annotation, exponent in annotations:
        annotation.set_rotation(power_law_angle(ax, exponent))
    figure.savefig(OUTPUT_PDF,bbox_inches="tight")
    plt.close(figure)
    print(f"Wrote {OUTPUT_PDF.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
