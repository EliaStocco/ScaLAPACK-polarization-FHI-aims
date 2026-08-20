#!/usr/bin/env python3

"""Standalone right-panel timing-contributions plot."""

import json

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker

from plot import BASE, DATA_FILE, STYLE_FILE


FIT_FILE = BASE / "power-law-fits.json"
OUTPUT_FILE = BASE / "scaling-right.pdf"


if STYLE_FILE.exists():
    plt.style.use(STYLE_FILE)


def clean_data(df, quantity):
    """Return valid positive x and y data."""

    subset = df[["atoms", quantity]].dropna()
    subset = subset[
        (subset["atoms"] > 0)
        & (subset[quantity] > 0)
    ].sort_values("atoms")

    return (
        subset["atoms"].to_numpy(dtype=float),
        subset[quantity].to_numpy(dtype=float),
    )


SCALAPACK_QUANTITIES = [
    "wannier_time",
    "fourier_ev_time",
    "dipole_matrix_time",
    "dipole_term_time",
    "berry_term_time",
]

LABELS = {
    "polarization_time": "Polarization",
    "wannier_time": "Polarization (total)",
    "fourier_ev_time": "Fourier interpolation",
    "dipole_matrix_time": "Dipole matrix",
    "dipole_term_time": "Dipole term",
    "berry_term_time": "Berry term",
    "converge_time": "Density convergence",
}


def plot_right_panel(ax, df, fits):
    """Plot individual timing contributions."""

    df = df[df["nodes"] == 2].copy()
    df = df[df["atoms"] != 686]

    scalapack = df[
        df["method"] == "scalapack"
    ].copy()

    # --------------------------------------------------------
    # Charge-density convergence
    # --------------------------------------------------------
    if (
        "converge_time" in df.columns
        and "converge_time" in fits
    ):

        quantity = "converge_time"

        converge = (
            df[["atoms", quantity]]
            .dropna()
            .drop_duplicates(subset=["atoms"])
            .sort_values("atoms")
        )

        x, y = clean_data(
            converge,
            quantity,
        )

        if len(x) > 0:

            # Main line + marker.
            #
            # This object is used for the legend.
            # alpha=0.8 applies to both here.
            line = ax.plot(
                x,
                y,
                marker="o",
                linestyle="-",
                alpha=0.8,
                label=LABELS.get(
                    quantity,
                    quantity,
                ),
            )[0]

            # Overlay fully opaque markers.
            #
            # These do NOT create another legend entry.
            ax.plot(
                x,
                y,
                linestyle="none",
                marker="o",
                color=line.get_color(),
                alpha=1.0,
                label="_nolegend_",
            )

    # --------------------------------------------------------
    # ScaLAPACK quantities
    # --------------------------------------------------------
    for quantity in SCALAPACK_QUANTITIES:

        if quantity not in scalapack.columns:
            continue

        if quantity not in fits:
            continue

        x, y = clean_data(
            scalapack,
            quantity,
        )

        if len(x) == 0:
            continue

        linestyle = (
            "-"
            if quantity == "wannier_time"
            else "--"
        )

        # Main line + marker.
        #
        # This object provides the legend handle.
        line = ax.plot(
            x,
            y,
            marker="o",
            linestyle=linestyle,
            alpha=0.8,
            label=LABELS.get(
                quantity,
                quantity,
            ),
        )[0]

        # Overlay opaque markers.
        ax.plot(
            x,
            y,
            linestyle="none",
            marker="o",
            color=line.get_color(),
            alpha=1.0,
            label="_nolegend_",
        )

    # --------------------------------------------------------
    # Axes
    # --------------------------------------------------------
    ax.set_xscale(
        "log",
        base=2,
    )

    ax.set_yscale(
        "log",
        base=10,
    )

    ax.set_xlabel("n. atoms")
    ax.set_ylabel("CPU time (s)")

    # --------------------------------------------------------
    # X ticks
    # --------------------------------------------------------
    xticks = sorted(
        df["atoms"].unique()
    )

    ax.xaxis.set_major_locator(
        mticker.FixedLocator(
            xticks
        )
    )

    ax.xaxis.set_major_formatter(
        mticker.FormatStrFormatter(
            "%d"
        )
    )

    ax.tick_params(
        axis="x",
        which="minor",
        length=3,
    )

    ax.tick_params(
        axis="x",
        which="major",
        length=4,
        labelrotation=35,
    )

    for label in ax.get_xticklabels():
        label.set_horizontalalignment(
            "right"
        )

    # --------------------------------------------------------
    # Legend
    # --------------------------------------------------------
    ax.legend(
        ncol=1,
    )

    # --------------------------------------------------------
    # Ideal cubic scaling guides
    # --------------------------------------------------------
    # add_cubic_scaling_lines(
    #     ax,
    #     n_lines=20,
    #     color="gray",
    #     alpha=0.5,
    #     linewidth=0.5,
    #     linestyle="--",
    # )
    
    xmin, xmax = sorted(ax.get_xlim())
    ymin, ymax = sorted(ax.get_ylim())
    # constants = [0.3,0.4,0.5]

    # More than 2 points gives smooth curves on linear axes
    x = np.logspace(np.log10(xmin), np.log10(xmax), 2)
    ax.plot(x, 0.3 * x, color="gray", alpha=0.5,linestyle="-" )
    for c in [1e-4]:
        ax.plot(x, c * x**2, color="gray", alpha=0.5,linestyle="-" )
    # ax.plot(x, 1e- * x**2, color="gray", alpha=0.5,linestyle="-" )
    
    ax.text(
        20, 7,
        r"linear scaling",
        # transform=ax.transAxes,
        rotation=9,      # angle in degrees
        ha="left",
        va="bottom",
        color="gray"
    )
    
    ax.text(
        400, 7,
        r"quadratic scaling",
        # transform=ax.transAxes,
        rotation=20,      # angle in degrees
        ha="left",
        va="bottom",
        color="gray"
    )
    
    ax.text(
        15, 400,
        r"ScaLAPACK",
        ha="left",
        va="bottom",
        bbox=dict(
            facecolor="white",
            edgecolor="black",
            boxstyle="round,pad=0.4",  # more space
            alpha=1,
        ),
    )

    ax.set_xlim(xmin, xmax)
    ax.set_ylim(ymin, ymax)

def main():
    df = pd.read_csv(DATA_FILE)

    if df.empty:
        raise RuntimeError(f"No data found in {DATA_FILE}")

    with FIT_FILE.open() as f:
        fits = json.load(f)

    fig, ax = plt.subplots(figsize=(6, 3.5))
    plot_right_panel(ax, df, fits)

    fig.tight_layout()
    fig.savefig(OUTPUT_FILE, bbox_inches="tight")

    print(f"Saved {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
