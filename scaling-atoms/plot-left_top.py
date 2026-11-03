#!/usr/bin/env python3

"""Plot only the upper (scaling) panel from the original two-panel figure.

Run ``extract.py`` first to create ``dataframe.csv``.
"""

import csv
from collections import Counter
from pathlib import Path

import matplotlib.image as mpimg
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
from matplotlib.offsetbox import AnnotationBbox, OffsetImage
import numpy as np


BASE = Path(__file__).resolve().parent
DATA_FILE = BASE / "dataframe.csv"
STYLE_FILE = BASE.parent / "style.mplstyle"
OUTPUT_FILE = BASE / "scaling-upper-only.pdf"

COLORS = {
    "lapack": "#1f77b4",
    "scalapack": "#ff7f0e",
}
METHOD_LABELS = {
    "lapack": "LAPACK",
    "scalapack": "ScaLAPACK",
}
FIT_LABEL_POSITIONS = {
    "lapack": (0.65, 0.61),
    "scalapack": (0.63, 0.32),
}
BLACS_LABEL_POSITIONS = {
    (2, 1): (0, 8, "bottom"),
    (2, 2): (0, -8, "top"),
    (4, 2): (2, 8, "bottom"),
    (5, 3): (7, 3, "bottom"),
    (13, 2): (7, 5, "bottom"),
    (43, 1): (14, 2, "bottom"),
    (8, 8): (-15, -2, "top"),
}


def to_float(value):
    return float(value) if value not in (None, "") else None


def load_data(path):
    with path.open(newline="") as handle:
        reader = csv.DictReader(handle)
        required = {
            "nodes", "atoms", "method", "dipole_time", "polarization_time",
            "allocated_cores", "polarization_cores",
            "polarization_cores_percentage", "blacs_grid_rows",
            "blacs_grid_columns",
        }
        missing = required - set(reader.fieldnames or ())
        if missing:
            raise ValueError(f"Missing columns in {path}: {sorted(missing)}")

        rows = []
        for raw in reader:
            try:
                row = {
                    "nodes": int(raw["nodes"]),
                    "atoms": int(raw["atoms"]),
                    "method": raw["method"],
                    "dipole_time": to_float(raw["dipole_time"]),
                    "polarization_time": to_float(raw["polarization_time"]),
                    "allocated_cores": int(raw["allocated_cores"]),
                    "polarization_cores": int(raw["polarization_cores"]),
                    "polarization_cores_percentage": to_float(
                        raw["polarization_cores_percentage"]
                    ),
                    "blacs_grid_rows": to_float(raw["blacs_grid_rows"]),
                    "blacs_grid_columns": to_float(raw["blacs_grid_columns"]),
                }
            except (TypeError, ValueError):
                continue

            if (
                row["nodes"] > 0
                and row["atoms"] > 0
                and row["method"] in METHOD_LABELS
                and row["dipole_time"] is not None
                and row["dipole_time"] > 0
                and row["polarization_time"] is not None
                and row["polarization_time"] > 0
                and row["allocated_cores"] > 0
                and 0 < row["polarization_cores"] <= row["allocated_cores"]
                and row["polarization_cores_percentage"] is not None
            ):
                rows.append(row)

    if not rows:
        raise RuntimeError(f"No valid timing data found in {path}")
    return rows


def primary_node_count(rows):
    return Counter(row["nodes"] for row in rows).most_common(1)[0][0]


def select(rows, **conditions):
    return sorted(
        (
            row for row in rows
            if all(row[key] == value for key, value in conditions.items())
        ),
        key=lambda row: row["atoms"],
    )


def set_atom_ticks(ax):
    ticks = [2**exponent for exponent in range(1, 11)]
    ax.set_xscale("log", base=2)
    ax.xaxis.set_major_locator(mticker.FixedLocator(ticks))
    ax.xaxis.set_major_formatter(mticker.FormatStrFormatter("%d"))
    ax.xaxis.set_minor_locator(mticker.NullLocator())
    ax.tick_params(axis="x", which="major", labelrotation=35)
    for label in ax.get_xticklabels():
        label.set_horizontalalignment("right")


def fit_power_law(xdata, ydata):
    exponent, log_amplitude = np.polyfit(np.log(xdata), np.log(ydata), 1)
    xfit = np.geomspace(min(xdata), max(xdata), 200)
    yfit = np.exp(log_amplitude) * xfit ** exponent
    return exponent, xfit, yfit


def power_law_angle(ax, exponent):
    xmin, xmax = ax.get_xlim()
    ymin, ymax = ax.get_ylim()
    x = np.sqrt(xmin * xmax)
    y = np.sqrt(ymin * ymax)
    scale = 1.1
    start, end = ax.transData.transform(((x, y), (x * scale, y * scale ** exponent)))
    return np.degrees(np.arctan2(end[1] - start[1], end[0] - start[0]))


def add_structure_image(ax, image_path, position, zoom):
    imagebox = OffsetImage(mpimg.imread(image_path), zoom=zoom)
    ax.add_artist(
        AnnotationBbox(
            imagebox,
            position,
            xycoords="axes fraction",
            frameon=False,
            zorder=2,
        )
    )


def plot_scaling(ax, rows, primary_nodes):
    fit_annotations = []
    plotted_points = {}
    for method in METHOD_LABELS:
        subset = select(rows, method=method, nodes=primary_nodes)
        if not subset:
            continue

        xdata = [row["atoms"] for row in subset]
        ydata = [row["polarization_time"] / 3600.0 for row in subset]
        plotted_points[method] = dict(zip(xdata, ydata))
        fit_xdata, fit_ydata = (
            (xdata[2:], ydata[2:]) if method == "lapack" else (xdata, ydata)
        )
        exponent, xfit, yfit = fit_power_law(fit_xdata, fit_ydata)
        ax.plot(
            xdata, ydata,
            color=COLORS[method],
            marker="o",
            markerfacecolor="white" if method == "lapack" else COLORS[method],
            markeredgecolor=COLORS[method],
            label=METHOD_LABELS[method],
        )
        ax.plot(
            xfit, yfit,
            color=COLORS[method],
            linestyle="--",
            alpha=0.6,
            label="_nolegend_",
        )
        annotation = ax.text(
            *FIT_LABEL_POSITIONS[method],
            rf"$m={exponent:.2f}$",
            transform=ax.transAxes,
            ha="center",
            va="center",
            color=COLORS[method],
        )
        fit_annotations.append((annotation, exponent))

    other_node_counts = sorted(
        {row["nodes"] for row in rows if row["nodes"] != primary_nodes}
    )
    for method in METHOD_LABELS:
        for nodes in other_node_counts:
            subset = select(rows, method=method, nodes=nodes)
            if not subset:
                continue
            ax.plot(
                [row["atoms"] for row in subset],
                [row["polarization_time"] / 3600.0 for row in subset],
                color=COLORS[method],
                marker="^",
                linestyle="none",
                label=f"{METHOD_LABELS[method]}, {nodes} nodes",
            )

    set_atom_ticks(ax)
    ax.set_yscale("log", base=2)
    ax.set_ylim(1.0 / 7200.0, 30.0)
    ax.set_xlabel("n. atoms")
    ax.set_ylabel("CPU time")
    ax.yaxis.set_major_locator(
        mticker.FixedLocator([1.0 / 3600.0, 1.0 / 60.0, 1.0, 24.0])
    )
    ax.yaxis.set_major_formatter(
        mticker.FixedFormatter(["1 s", "1 m", "1 h", "1 day"])
    )
    image_positions = {
        "small": (0.1, 0.30),
        "medium": (0.35, 0.55),
        "large": (0.75, 0.20),
    }
    add_structure_image(ax, BASE / "supercell.2.png", image_positions["small"], 0.015)
    add_structure_image(ax, BASE / "supercell.4.png", image_positions["medium"], 0.030)
    add_structure_image(ax, BASE / "supercell.8.png", image_positions["large"], 0.055)
    arrow_tails = {
        "small": (0.13, 0.3),
        "medium": (0.42, 0.52),
        "large": (0.9, 0.35),
    }
    arrow_style = {
        "arrowstyle": "-|>",
        "color": "gray",
        "connectionstyle": "angle3,angleA=180,angleB=90",
        "mutation_scale": 8,
        "shrinkA": 4,
        "shrinkB": 2,
    }
    for arrow_tail, point in (
        (arrow_tails["small"], (16, plotted_points["lapack"][16])),
        (arrow_tails["medium"], (128, plotted_points["lapack"][128])),
        (arrow_tails["large"], (1024, plotted_points["scalapack"][1024])),
    ):
        ax.annotate(
            "",
            xy=point,
            xycoords="data",
            xytext=arrow_tail,
            textcoords="axes fraction",
            arrowprops=arrow_style,
            zorder=4,
        )
    ax.legend()
    return fit_annotations


def main():
    if STYLE_FILE.exists():
        plt.style.use(STYLE_FILE)

    rows = load_data(DATA_FILE)
    primary_nodes = primary_node_count(rows)

    # The upper panel occupied 3/4 of the original 4 × 5.25 figure height.
    # Reproducing that exact physical size keeps fonts and line weights identical.
    fig, ax = plt.subplots(figsize=(4, 5.25 * 3 / 4), layout="constrained")

    fit_annotations = plot_scaling(ax, rows, primary_nodes)

    fig.canvas.draw()
    for annotation, exponent in fit_annotations:
        annotation.set_rotation(power_law_angle(ax, exponent))

    fig.savefig(OUTPUT_FILE, bbox_inches="tight")
    print(f"Saved {OUTPUT_FILE}")


if __name__ == "__main__":
    main()