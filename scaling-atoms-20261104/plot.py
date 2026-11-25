#!/usr/bin/env python3
"""Plot the atom-scaling comparison with updated ScaLAPACK timings."""

from __future__ import annotations

import csv
from pathlib import Path

import matplotlib.image as mpimg
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
from matplotlib.offsetbox import AnnotationBbox, OffsetImage
import numpy as np


BASE = Path(__file__).resolve().parent
DATA_FILE = BASE / "dataframe.csv"
STYLE_FILE = BASE / "style.mplstyle"
OUTPUT_FILE = BASE / "scaling-atoms-20261104.pdf"
COLORS = {"lapack": "#1f77b4", "scalapack": "#ff7f0e"}
LABELS = {"lapack": "LAPACK", "scalapack": "ScaLAPACK"}
FIT_LABEL_POSITIONS = {"lapack": (0.65, 0.61), "scalapack": (0.63, 0.32)}


def load_data() -> list[dict[str, object]]:
    with DATA_FILE.open(newline="") as handle:
        reader = csv.DictReader(handle)
        rows = []
        for raw in reader:
            rows.append(
                {
                    "atoms": int(raw["atoms"]),
                    "method": raw["method"],
                    "polarization_time": float(raw["polarization_time"]),
                }
            )
    if not rows:
        raise RuntimeError(f"No data found in {DATA_FILE}")
    return rows


def fit_power_law(xdata: list[int], ydata: list[float]) -> tuple[float, np.ndarray, np.ndarray]:
    exponent, log_amplitude = np.polyfit(np.log(xdata), np.log(ydata), 1)
    xfit = np.geomspace(min(xdata), max(xdata), 200)
    return exponent, xfit, np.exp(log_amplitude) * xfit**exponent


def power_law_angle(ax, exponent: float) -> float:
    xmin, xmax = ax.get_xlim()
    ymin, ymax = ax.get_ylim()
    x, y = np.sqrt(xmin * xmax), np.sqrt(ymin * ymax)
    start, end = ax.transData.transform(((x, y), (x * 1.1, y * 1.1**exponent)))
    return np.degrees(np.arctan2(end[1] - start[1], end[0] - start[0]))


def add_structure_image(ax, name: str, position: tuple[float, float], zoom: float) -> None:
    image = OffsetImage(mpimg.imread(BASE / name), zoom=zoom)
    ax.add_artist(AnnotationBbox(image, position, xycoords="axes fraction", frameon=False, zorder=2))


def main() -> None:
    if STYLE_FILE.exists():
        plt.style.use(STYLE_FILE)
    rows = load_data()
    fig, ax = plt.subplots(figsize=(4, 5.25 * 3 / 4), layout="constrained")
    annotations = []
    points: dict[str, dict[int, float]] = {}
    for method in ("lapack", "scalapack"):
        subset = sorted((row for row in rows if row["method"] == method), key=lambda row: row["atoms"])
        xdata = [int(row["atoms"]) for row in subset]
        ydata = [float(row["polarization_time"]) / 3600 for row in subset]
        points[method] = dict(zip(xdata, ydata))
        # Retain the original LAPACK fit convention: omit the two smallest cells.
        fit_x, fit_y = (xdata[2:], ydata[2:]) if method == "lapack" else (xdata, ydata)
        exponent, xfit, yfit = fit_power_law(fit_x, fit_y)
        ax.plot(
            xdata, ydata, color=COLORS[method], marker="o",
            markerfacecolor="white" if method == "lapack" else COLORS[method],
            markeredgecolor=COLORS[method], label=LABELS[method],
        )
        ax.plot(xfit, yfit, color=COLORS[method], linestyle="--", alpha=0.6)
        annotation = ax.text(*FIT_LABEL_POSITIONS[method], rf"$m={exponent:.2f}$", transform=ax.transAxes, ha="center", va="center", color=COLORS[method])
        annotations.append((annotation, exponent))

    ticks = [2**power for power in range(1, 11)]
    ax.set_xscale("log", base=2)
    ax.xaxis.set_major_locator(mticker.FixedLocator(ticks))
    ax.xaxis.set_major_formatter(mticker.FormatStrFormatter("%d"))
    ax.xaxis.set_minor_locator(mticker.NullLocator())
    ax.tick_params(axis="x", which="major", labelrotation=35)
    for label in ax.get_xticklabels():
        label.set_horizontalalignment("right")
    ax.set_yscale("log", base=2)
    ax.set_ylim(1 / 7200, 30)
    ax.set_xlabel("n. atoms")
    ax.set_ylabel("CPU time")
    ax.yaxis.set_major_locator(mticker.FixedLocator([1 / 3600, 1 / 60, 1, 24]))
    ax.yaxis.set_major_formatter(mticker.FixedFormatter(["1 s", "1 m", "1 h", "1 day"]))

    add_structure_image(ax, "supercell.2.png", (0.1, 0.30), 0.015)
    add_structure_image(ax, "supercell.4.png", (0.35, 0.55), 0.030)
    add_structure_image(ax, "supercell.8.png", (0.75, 0.20), 0.055)
    arrow_style = {"arrowstyle": "-|>", "color": "gray", "connectionstyle": "angle3,angleA=180,angleB=90", "mutation_scale": 8, "shrinkA": 4, "shrinkB": 2}
    for tail, point in (((0.13, 0.3), (16, points["lapack"][16])), ((0.42, 0.52), (128, points["lapack"][128])), ((0.9, 0.35), (1024, points["scalapack"][1024]))):
        ax.annotate("", xy=point, xycoords="data", xytext=tail, textcoords="axes fraction", arrowprops=arrow_style, zorder=4)
    ax.legend()
    fig.canvas.draw()
    for annotation, exponent in annotations:
        annotation.set_rotation(power_law_angle(ax, exponent))
    fig.savefig(OUTPUT_FILE, bbox_inches="tight")
    print(f"Saved {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
