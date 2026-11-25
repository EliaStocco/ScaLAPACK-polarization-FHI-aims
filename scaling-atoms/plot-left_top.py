#!/usr/bin/env python3

"""Plot only the upper (scaling) panel from the original two-panel figure.

Run ``extract.py`` first to create ``dataframe.csv``.
"""

import csv
from collections import Counter
from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np

from plotting_helpers import configure_log_atom_axis


BASE = Path(__file__).resolve().parent
DATA_FILE = BASE / "dataframe.csv"
STYLE_FILE = BASE.parent / "style.mplstyle"
OUTPUT_FILE = BASE / "Figure-6.pdf"
SELECTED_ATOM_COUNTS = frozenset((4, 16, 64, 256, 1024))
IDEAL_LABEL_POSITION = (4, 1.0 / 60.0)

COLORS = {
    "lapack": "#1f77b4",
    "scalapack": "#ff7f0e",
}
METHOD_LABELS = {
    "lapack": r"\texttt{LAPACK}",
    "scalapack": r"\texttt{ScaLAPACK}",
}
FIT_LABEL_POSITIONS = {
    "lapack": ((0.20, 0.2), (0.76, 0.8)),
    "scalapack": (0.60, 0.28),
}
FIT_LINE_PADDING = 1.5
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
                and row["atoms"] in SELECTED_ATOM_COUNTS
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


def fit_power_law(xdata, ydata, xfit_min=None, xfit_max=None):
    exponent, log_amplitude = np.polyfit(np.log(xdata), np.log(ydata), 1)
    xfit = np.geomspace(
        min(xdata) if xfit_min is None else xfit_min,
        max(xdata) if xfit_max is None else xfit_max,
        200,
    )
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


def add_ideal_scaling_lines(ax, n_lines=10):
    """Draw reference lines for ideal linear scaling, ``y = A x``."""

    xmin, xmax = sorted(ax.get_xlim())
    ymin, ymax = sorted(ax.get_ylim())
    x = np.geomspace(xmin, xmax, 200)
    log_step = np.log((ymax / xmin) / (ymin / xmax)) / (n_lines - 1)
    label_amplitude = IDEAL_LABEL_POSITION[1] / IDEAL_LABEL_POSITION[0]
    label_index = n_lines // 2
    amplitudes = label_amplitude * np.exp(
        log_step * (np.arange(n_lines) - label_index)
    )
    for amplitude in amplitudes:
        ax.plot(
            x,
            amplitude * x,
            color="gray",
            alpha=0.5,
            linewidth=0.5,
            linestyle="--",
            zorder=0,
        )
    ax.set_xlim(xmin, xmax)
    ax.set_ylim(ymin, ymax)


def plot_scaling(ax, rows, primary_nodes):
    fit_annotations = []
    primary_subsets = {
        method: select(rows, method=method, nodes=primary_nodes)
        for method in METHOD_LABELS
    }
    common_xmin = max(min(row["atoms"] for row in subset) for subset in primary_subsets.values())
    common_xmax = min(max(row["atoms"] for row in subset) for subset in primary_subsets.values())
    for method in METHOD_LABELS:
        subset = primary_subsets[method]
        if not subset:
            continue

        xdata = [row["atoms"] for row in subset]
        ydata = [row["polarization_time"] / 3600.0 for row in subset]
        ax.plot(
            xdata, ydata,
            color=COLORS[method],
            marker="o",
            markerfacecolor="white" if method == "lapack" else COLORS[method],
            markeredgecolor=COLORS[method],
            label=METHOD_LABELS[method],
        )
        if method == "lapack":
            fit_specs = (
                ([x for x in xdata if x <= 64], [y for x, y in zip(xdata, ydata) if x <= 64], 4 / FIT_LINE_PADDING, 64 * FIT_LINE_PADDING, FIT_LABEL_POSITIONS["lapack"][0]),
                ([x for x in xdata if x >= 64], [y for x, y in zip(xdata, ydata) if x >= 64], 64 / FIT_LINE_PADDING, 1024 * FIT_LINE_PADDING, FIT_LABEL_POSITIONS["lapack"][1]),
            )
        else:
            fit_specs = ((xdata, ydata, common_xmin / FIT_LINE_PADDING, common_xmax * FIT_LINE_PADDING, FIT_LABEL_POSITIONS[method]),)
        for fit_xdata, fit_ydata, xfit_min, xfit_max, label_position in fit_specs:
            exponent, xfit, yfit = fit_power_law(fit_xdata, fit_ydata, xfit_min, xfit_max)
            ax.plot(xfit, yfit, color=COLORS[method], linestyle="--", alpha=0.6, label="_nolegend_")
            annotation = ax.text(
                *label_position, rf"$m={exponent:.2f}$", transform=ax.transAxes,
                ha="center", va="center", color=COLORS[method],
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

    configure_log_atom_axis(ax, SELECTED_ATOM_COUNTS, margin_factor=1.5)
    ax.set_yscale("log", base=2)
    ax.set_ylim(1.0 / 7200.0, 30.0)
    add_ideal_scaling_lines(ax)
    ideal_annotation = ax.annotate(
        r"ideal scaling: $m=1$",
        xy=IDEAL_LABEL_POSITION,
        xycoords="data",
        xytext=(0, 4),
        textcoords="offset points",
        ha="left",
        va="bottom",
        color="gray",
    )
    fit_annotations.append((ideal_annotation, 1.0))
    ax.set_xlabel("n. atoms")
    ax.set_ylabel("CPU time")
    ax.yaxis.set_major_locator(
        mticker.FixedLocator([1.0 / 3600.0, 1.0 / 60.0, 1.0, 24.0])
    )
    ax.yaxis.set_major_formatter(
        mticker.FixedFormatter(["1 s", "1 m", "1 h", "1 day"])
    )
    ax.legend(loc="upper left")
    return fit_annotations


def main():
    if STYLE_FILE.exists():
        plt.style.use(STYLE_FILE)

    rows = load_data(DATA_FILE)
    primary_nodes = primary_node_count(rows)

    # Match the 4 × 4 inch physical figure size used for Figure 5.
    fig, ax = plt.subplots(figsize=(4, 4))
    fig.subplots_adjust(left=0.20, right=0.98, bottom=0.16, top=0.98)

    fit_annotations = plot_scaling(ax, rows, primary_nodes)

    fig.canvas.draw()
    for annotation, exponent in fit_annotations:
        annotation.set_rotation(power_law_angle(ax, exponent))

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUTPUT_FILE)
    print(f"Saved {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
