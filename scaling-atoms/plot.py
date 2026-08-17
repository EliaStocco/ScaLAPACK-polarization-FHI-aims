#!/usr/bin/env python3

"""Plot polarization wall time versus number of atoms."""

import csv
from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.ticker as mticker


BASE = Path(__file__).resolve().parent
DATA_FILE = BASE / "dataframe.csv"
STYLE_FILE = BASE.parent / "style.mplstyle"
OUTPUT_FILE = BASE / "scaling.pdf"

COLORS = {
    "lapack": "#1f77b4",
    "scalapack": "#ff7f0e",
}

METHOD_LABELS = {
    "lapack": "LAPACK",
    "scalapack": "ScaLAPACK",
}

NODE_STYLES = {
    2: {"marker": "o", "linestyle": "-"},
    4: {"marker": "s", "linestyle": "--"},
}

import pandas as pd


def load_data(path):
    required = {
        "nodes",
        "supercell",
        "atoms",
        "method",
        "scf_time",
        "dipole_time",
        "polarization_time",
    }

    df = pd.read_csv(path)

    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Missing columns in {path}: {sorted(missing)}")

    df = df.astype({
        "nodes": int,
        "supercell": int,
        "atoms": int,
        "method": str,
        "scf_time": float,
        "dipole_time": float,
        "polarization_time": float,
    })
    
    df = df[df["atoms"] != 686]

    return df.sort_values(["method", "nodes", "atoms"]).to_dict("records")


def plot(rows):
    fig, (ax, speedup_ax) = plt.subplots(
        2,
        1,
        sharex=True,
        figsize=(4.5, 3.8),
        gridspec_kw={"height_ratios": (3, 1), "hspace": 0.08},
    )
    fig.set_layout_engine(None)
    fig.set_tight_layout(False)

    for method in ("lapack", "scalapack"):
        for nodes in (2, 4):
            subset = sorted(
                (
                    row
                    for row in rows
                    if row["method"] == method and row["nodes"] == nodes
                ),
                key=lambda row: row["atoms"],
            )
            if not subset:
                continue

            style = NODE_STYLES[nodes]
            ax.plot(
                [row["atoms"] for row in subset],
                [row["polarization_time"] / 3600.0 for row in subset],
                color=COLORS[method],
                marker=style["marker"],
                linestyle=style["linestyle"],
                linewidth=1.2,
                markersize=4,
                label=f"{METHOD_LABELS[method]}, {nodes} nodes",
            )

    ax.set_xscale("log", base=2)
    ax.set_yscale("log", base=2)
    ax.set_ylim(1.0 / 4500.0, 30.0)
    ax.set_ylabel("CPU time (h)")

    time_ticks = [1.0 / 3600.0, 1.0 / 60.0, 1.0, 24.0]
    time_labels = ["1 s", "1 m", "1 h", "1 day"]
    ax.yaxis.set_major_locator(mticker.FixedLocator(time_ticks))
    ax.yaxis.set_major_formatter(mticker.FixedFormatter(time_labels))

    legend = ax.legend(loc="best")
    legend.get_frame().set_facecolor("white")
    legend.get_frame().set_edgecolor("black")
    legend.get_frame().set_alpha(1.0)

    for method in ("lapack", "scalapack"):
        times_by_nodes = {
            nodes: {
                row["atoms"]: row["polarization_time"]
                for row in rows
                if row["method"] == method and row["nodes"] == nodes
            }
            for nodes in (2, 4)
        }
        common_atoms = sorted(
            set(times_by_nodes[2]).intersection(times_by_nodes[4])
        )
        if not common_atoms:
            continue

        speedup = [
            times_by_nodes[2][atoms] / times_by_nodes[4][atoms]
            for atoms in common_atoms
        ]
        speedup_ax.plot(
            common_atoms,
            speedup,
            color=COLORS[method],
            marker="o",
            linewidth=1.0,
            markersize=3,
            label=METHOD_LABELS[method],
        )

    speedup_ax.axhline(1.0, color="0.4", linestyle=":", linewidth=0.8)
    speedup_ax.set_xscale("log", base=2)
    speedup_ax.set_ylim(0.9, 2.35)
    speedup_ax.set_xlabel("n. atoms")
    speedup_ax.set_ylabel("speedup")
    speedup_ax.text(
        0.03,
        0.92,
        "2 $\\rightarrow$ 4 nodes",
        transform=speedup_ax.transAxes,
        ha="left",
        va="top",
        fontsize=8,
    )
    speedup_ax.yaxis.set_major_locator(mticker.FixedLocator([1.0, 1.5, 2.0]))

    xticks = sorted({row["atoms"] for row in rows})
    speedup_ax.xaxis.set_major_locator(mticker.FixedLocator(xticks))
    speedup_ax.xaxis.set_major_formatter(mticker.FormatStrFormatter("%d"))
    speedup_ax.tick_params(axis="x", which="minor", length=3)
    speedup_ax.tick_params(
        axis="x", which="major", length=4, labelrotation=35
    )
    for label in speedup_ax.get_xticklabels():
        label.set_horizontalalignment("right")

    fig.subplots_adjust(left=0.16, right=0.98, bottom=0.16, top=0.97)
    return fig


def main():
    if STYLE_FILE.exists():
        plt.style.use(STYLE_FILE)
    plt.rcParams["figure.autolayout"] = False

    rows = load_data(DATA_FILE)
    if not rows:
        raise RuntimeError(f"No data found in {DATA_FILE}")

    figure = plot(rows)
    figure.savefig(OUTPUT_FILE, bbox_inches="tight")
    print(f"Saved {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
