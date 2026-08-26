#!/usr/bin/env python3

"""Plot the ScaLAPACK timing components as a function of atom count.

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
OUTPUT_FILE = BASE / "scaling-right.pdf"

RAW_QUANTITIES = [
    "converge_time",
    "polarization_time",
    "wannier_time",
    "fourier_ev_time",
    "dipole_matrix_time",
    "dipole_term_time",
    "berry_term_time",
    # "scf_time",
]
QUANTITIES = [
    "converge_time",
    "polarization_time",
    "fourier_ev_time",
    "dipole_matrix_time",
    "dipole_term_time",
    "berry_term_time",
    "extra_time",
]
LABELS = {
    "converge_time": "Density convergence",
    # This is the same dipole-minus-SCF quantity used for the ScaLAPACK
    # (orange) curve in plot_left.py.
    "polarization_time": "Polarization (total)",
    "extra_time": "Extra",
    "fourier_ev_time": "Fourier interpolation",
    "dipole_matrix_time": "Dipole matrix",
    "dipole_term_time": "Dipole term",
    "berry_term_time": "Berry term",
    "scf_time": "1 SCF cycle",
}
COLORS = {
    "converge_time": "#0173b2",
    "polarization_time": "#de8f05",
    "fourier_ev_time": "#d55e00",
    "dipole_matrix_time": "#cc78bc",
    "dipole_term_time": "#ca9161",
    "berry_term_time": "#7a7a7a",
    "extra_time": "#029e73",
}
MARKERS = {
    "converge_time": "o",
    "polarization_time": "s",
    "fourier_ev_time": "^",
    "dipole_matrix_time": "D",
    "dipole_term_time": "v",
    "berry_term_time": "P",
    "extra_time": "X",
}


def to_float(value):
    """Convert a CSV value to float, keeping empty values as ``None``."""
    return float(value) if value not in (None, "") else None


def load_data(path):
    """Load valid ScaLAPACK rows from the timing CSV."""
    with path.open(newline="") as handle:
        reader = csv.DictReader(handle)
        required = {"nodes", "atoms", "method", *RAW_QUANTITIES}
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
                }
                for quantity in RAW_QUANTITIES:
                    row[quantity] = to_float(raw[quantity])
                if (
                    row["polarization_time"] is not None
                    and row["wannier_time"] is not None
                ):
                    # The signed residual is retained as untracked_time by
                    # extract.py.  Plot its absolute magnitude because the
                    # logarithmic y axis cannot represent negative values.
                    row["extra_time"] = abs(
                        row["polarization_time"] - row["wannier_time"]
                    )
                else:
                    row["extra_time"] = None
            except (TypeError, ValueError):
                continue

            if (
                row["nodes"] > 0
                and row["atoms"] > 0
                and row["method"] == "scalapack"
            ):
                rows.append(row)

    if not rows:
        raise RuntimeError(f"No valid ScaLAPACK timing data found in {path}")
    return rows


def primary_node_count(rows):
    """Select the node count with the most ScaLAPACK results."""
    return Counter(row["nodes"] for row in rows).most_common(1)[0][0]


def set_atom_ticks(ax, atoms):
    """Format a base-two atom-count axis using the measured values."""
    ticks = sorted(set(atoms))
    ax.set_xscale("log", base=2)
    ax.xaxis.set_major_locator(mticker.FixedLocator(ticks))
    ax.xaxis.set_major_formatter(mticker.FormatStrFormatter("%d"))
    ax.xaxis.set_minor_locator(mticker.NullLocator())
    ax.tick_params(axis="x", which="major", labelrotation=35)
    for label in ax.get_xticklabels():
        label.set_horizontalalignment("right")


def plot_components(ax, rows, primary_nodes):
    """Plot individual timing contributions for ScaLAPACK."""
    scalapack = sorted(
        (row for row in rows if row["nodes"] == primary_nodes),
        key=lambda row: row["atoms"],
    )
    if not scalapack:
        raise RuntimeError("No ScaLAPACK timings are available for the main node count")

    plotted_atoms = []
    for quantity in QUANTITIES:
        subset = [
            row
            for row in scalapack
            if row[quantity] is not None and row[quantity] > 0
        ]
        if not subset:
            continue

        plotted_atoms.extend(row["atoms"] for row in subset)
        ax.plot(
            [row["atoms"] for row in subset],
            [row[quantity] for row in subset],
            color=COLORS[quantity],
            marker=MARKERS[quantity],
            linestyle="-"
            if quantity in {"converge_time", "polarization_time"}
            else "--",
            label=LABELS[quantity],
        )

    if not plotted_atoms:
        raise RuntimeError("No ScaLAPACK component timings are available")

    set_atom_ticks(ax, plotted_atoms)
    ax.set_yscale("log")
    ax.set_xlabel("n. atoms")
    ax.set_ylabel("Wall-clock time (s)")
    ax.legend()

    xmin, xmax = ax.get_xlim()
    guide_x = [8, 1300]
    print(guide_x)
    ax.plot(guide_x, [0.3 * value for value in guide_x], color="gray", alpha=0.5)
    ax.plot(
        guide_x,
        [1e-4 * value**2 for value in guide_x],
        color="gray",
        alpha=0.5,
    )
    arrow_style = {
        "arrowstyle": "-|>",
        "color": "gray",
        "connectionstyle": "angle3,angleA=180,angleB=90",
        "mutation_scale": 8,
        "shrinkA": 4,
        "shrinkB": 2,
    }
    linear_target_x = 14
    ax.annotate(
        "linear scaling",
        xy=(linear_target_x, 0.3 * linear_target_x),
        xycoords="data",
        xytext=(0.10, 0.73),
        textcoords="axes fraction",
        color="gray",
        arrowprops=arrow_style,
    )
    quadratic_target_x = 14
    ax.annotate(
        "quadratic scaling",
        xy=(quadratic_target_x, 1e-4 * quadratic_target_x**2),
        xycoords="data",
        xytext=(0.10, 0.08),
        textcoords="axes fraction",
        color="gray",
        arrowprops=arrow_style,
    )
    ax.set_xlim(xmin, xmax)
    ax.set_ylim(1e-3, 1e3)


def main():
    if STYLE_FILE.exists():
        plt.style.use(STYLE_FILE)

    rows = load_data(DATA_FILE)
    primary_nodes = primary_node_count(rows)
    fig, ax = plt.subplots(figsize=(6, 3.5))
    plot_components(ax, rows, primary_nodes)
    fig.savefig(OUTPUT_FILE, bbox_inches="tight")
    print(f"Saved {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
