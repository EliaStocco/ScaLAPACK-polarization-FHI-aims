#!/usr/bin/env python3

"""Plot LAPACK and ScaLAPACK timings as a function of atom count.

Run ``extract.py`` first to create ``dataframe.csv``.
"""

import csv
from collections import Counter
from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.ticker as mticker


BASE = Path(__file__).resolve().parent
DATA_FILE = BASE / "dataframe.csv"
STYLE_FILE = BASE.parent / "style.mplstyle"
OUTPUT_FILE = BASE / "scaling-left.pdf"

COLORS = {
    "lapack": "#1f77b4",
    "scalapack": "#ff7f0e",
}
METHOD_LABELS = {
    "lapack": "LAPACK",
    "scalapack": "ScaLAPACK",
}
# Explicit text positions: (horizontal offset, vertical offset, alignment).
# Offsets are measured in points relative to the corresponding data point.
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
    """Convert a CSV value to float, keeping empty values as ``None``."""
    return float(value) if value not in (None, "") else None


def load_data(path):
    """Load valid rows from the timing CSV."""
    with path.open(newline="") as handle:
        reader = csv.DictReader(handle)
        required = {
            "nodes",
            "atoms",
            "method",
            "dipole_time",
            "polarization_time",
            "blacs_grid_rows",
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
            ):
                rows.append(row)

    if not rows:
        raise RuntimeError(f"No valid timing data found in {path}")
    return rows


def primary_node_count(rows):
    """Select the node count with the most results for the main curves."""
    return Counter(row["nodes"] for row in rows).most_common(1)[0][0]


def select(rows, **conditions):
    """Filter and sort timing rows by atom count."""
    return sorted(
        (
            row
            for row in rows
            if all(row[key] == value for key, value in conditions.items())
        ),
        key=lambda row: row["atoms"],
    )


def set_atom_ticks(ax):
    """Format the atom-count axis with powers of two from 8 to 1024."""
    ticks = [2**exponent for exponent in range(1, 11)]
    ax.set_xscale("log", base=2)
    ax.xaxis.set_major_locator(mticker.FixedLocator(ticks))
    ax.xaxis.set_major_formatter(mticker.FormatStrFormatter("%d"))
    ax.xaxis.set_minor_locator(mticker.NullLocator())
    ax.tick_params(axis="x", which="major", labelrotation=35)
    for label in ax.get_xticklabels():
        label.set_horizontalalignment("right")


def plot_scaling(ax, rows, primary_nodes):
    """Plot the total cost for each linear-algebra method."""
    for method in METHOD_LABELS:
        subset = select(rows, method=method, nodes=primary_nodes)
        if not subset:
            continue

        xdata = [row["atoms"] for row in subset]
        ydata = [row["polarization_time"] / 3600.0 for row in subset]
        ax.plot(
            xdata,
            ydata,
            color=COLORS[method],
            marker="o",
            label=METHOD_LABELS[method],
        )

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
    ax.legend()


def plot_blacs_grid_balance(ax, rows, primary_nodes):
    """Plot how closely the BLACS grid dimensions approach a square."""
    subset = [
        row
        for row in select(rows, method="scalapack", nodes=primary_nodes)
        if row["blacs_grid_rows"] is not None
        and row["blacs_grid_columns"] is not None
    ]
    if not subset:
        raise RuntimeError("No BLACS grid dimensions are available")

    atoms = [row["atoms"] for row in subset]
    balances = [
        1.0
        - abs(row["blacs_grid_rows"] - row["blacs_grid_columns"])
        / (row["blacs_grid_rows"] + row["blacs_grid_columns"])
        for row in subset
    ]
    ax.plot(
        atoms,
        balances,
        color=COLORS["scalapack"],
        marker="o",
    )
    for row, balance in zip(subset, balances):
        grid = (
            int(row["blacs_grid_rows"]),
            int(row["blacs_grid_columns"]),
        )
        grid_label = rf"${grid[0]}\!\times\!{grid[1]}$"
        x_offset, y_offset, vertical_alignment = BLACS_LABEL_POSITIONS[grid]
        ax.annotate(
            grid_label,
            (row["atoms"], balance),
            xytext=(x_offset, y_offset),
            textcoords="offset points",
            ha="center",
            va=vertical_alignment,
            fontsize=8,
            zorder=3,
        )
    ax.axhline(1.0, color="gray", linestyle="--")
    ax.axhline(0.0, color="gray", linestyle="--")
    set_atom_ticks(ax)
    ax.set_ylim(-0.05, 1.05)
    ax.yaxis.set_major_locator(mticker.FixedLocator([0.0, 0.5, 1.0]))
    ax.yaxis.set_major_formatter(mticker.PercentFormatter(xmax=1.0))
    ax.set_xlabel("n. atoms")
    ax.set_ylabel("BLACS balance")


def main():
    if STYLE_FILE.exists():
        plt.style.use(STYLE_FILE)

    rows = load_data(DATA_FILE)
    primary_nodes = primary_node_count(rows)
    fig, (ax_scaling, ax_balance) = plt.subplots(
        2,
        1,
        figsize=(3, 4),
        sharex=True,
        gridspec_kw={"height_ratios": [3, 1]},
    )
    plot_scaling(ax_scaling, rows, primary_nodes)
    ax_scaling.set_xlabel("")
    ax_scaling.tick_params(axis="x", labelbottom=False)
    plot_blacs_grid_balance(ax_balance, rows, primary_nodes)
    fig.savefig(OUTPUT_FILE, bbox_inches="tight")
    print(f"Saved {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
