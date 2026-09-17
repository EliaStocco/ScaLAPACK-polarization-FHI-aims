#!/usr/bin/env python3

"""Plot ideal polarization cost if every allocated MPI rank is active.

Run ``extract.py`` first to create ``dataframe.csv``.  For each calculation,
the ideal 100%-activity wall time is the measured wall time scaled by the
active-rank fraction.  Multiplying that time by all allocated ranks gives the
same cost as the measured wall time multiplied by only the active ranks.
"""

import csv
from collections import Counter
from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.ticker as mticker


BASE = Path(__file__).resolve().parent
DATA_FILE = BASE / "dataframe.csv"
STYLE_FILE = BASE.parent / "style.mplstyle"
OUTPUT_FILE = BASE / "scaling-full-activity-cost.pdf"

COLORS = {
    "lapack": "#1f77b4",
    "scalapack": "#ff7f0e",
}
METHOD_LABELS = {
    "lapack": "LAPACK",
    "scalapack": "ScaLAPACK",
}


def to_float(value):
    """Convert a CSV value to float, keeping empty values as ``None``."""
    return float(value) if value not in (None, "") else None


def load_data(path):
    """Load timing and active-rank data from the extraction CSV."""
    with path.open(newline="") as handle:
        reader = csv.DictReader(handle)
        required = {
            "nodes",
            "atoms",
            "method",
            "allocated_cores",
            "polarization_cores",
            "polarization_time",
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
                    "allocated_cores": int(raw["allocated_cores"]),
                    "polarization_cores": int(raw["polarization_cores"]),
                    "polarization_time": to_float(raw["polarization_time"]),
                }
            except (TypeError, ValueError):
                continue

            if (
                row["nodes"] > 0
                and row["atoms"] > 0
                and row["method"] in METHOD_LABELS
                and row["allocated_cores"] > 0
                and 0 < row["polarization_cores"] <= row["allocated_cores"]
                and row["polarization_time"] is not None
                and row["polarization_time"] > 0
            ):
                rows.append(row)

    if not rows:
        raise RuntimeError(f"No valid polarization data found in {path}")
    return rows


def primary_node_count(rows):
    """Select the node count with the most results for the main curves."""
    return Counter(row["nodes"] for row in rows).most_common(1)[0][0]


def select(rows, method, nodes):
    """Return a method/node subset sorted by atom count."""
    return sorted(
        (
            row
            for row in rows
            if row["method"] == method and row["nodes"] == nodes
        ),
        key=lambda row: row["atoms"],
    )


def ideal_core_hours(row):
    """Return the cost for the same work with no allocated-rank idling."""
    ideal_wall_time = (
        row["polarization_time"]
        * row["polarization_cores"]
        / row["allocated_cores"]
    )
    return row["allocated_cores"] * ideal_wall_time / 3600.0


def set_atom_ticks(ax):
    """Format the atom-count axis with powers of two from 2 to 1024."""
    ticks = [2**exponent for exponent in range(1, 11)]
    ax.set_xscale("log", base=2)
    ax.xaxis.set_major_locator(mticker.FixedLocator(ticks))
    ax.xaxis.set_major_formatter(mticker.FormatStrFormatter("%d"))
    ax.xaxis.set_minor_locator(mticker.NullLocator())
    ax.tick_params(axis="x", which="major", labelrotation=35)
    for label in ax.get_xticklabels():
        label.set_horizontalalignment("right")


def plot_full_activity_cost(ax, rows, primary_nodes):
    """Plot the ideal 100%-activity cost for each method."""
    for method in METHOD_LABELS:
        subset = select(rows, method, primary_nodes)
        if not subset:
            continue
        ax.plot(
            [row["atoms"] for row in subset],
            [ideal_core_hours(row) for row in subset],
            color=COLORS[method],
            marker="o",
            label=METHOD_LABELS[method],
        )

    set_atom_ticks(ax)
    ax.set_yscale("log")
    ax.set_xlabel("n. atoms")
    ax.set_ylabel("Ideal cost (core h)")
    ax.legend()


def main():
    if STYLE_FILE.exists():
        plt.style.use(STYLE_FILE)

    rows = load_data(DATA_FILE)
    fig, ax = plt.subplots(figsize=(4, 3))
    plot_full_activity_cost(ax, rows, primary_node_count(rows))
    fig.savefig(OUTPUT_FILE, bbox_inches="tight")
    print(f"Saved {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
