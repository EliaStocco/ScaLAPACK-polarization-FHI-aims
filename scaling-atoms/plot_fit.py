#!/usr/bin/env python3

"""Plot all two-node atom-scaling timings and power-law fits."""

import json
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
BASE = Path(__file__).resolve().parent
DATA_FILE = BASE / "dataframe.csv"
STYLE_FILE = BASE.parent / "style.mplstyle"
plt.style.use(STYLE_FILE)

DATA_FILE = BASE / "dataframe.csv"
FIT_FILE = BASE / "power-law-fits.json"
OUTPUT_FILE = BASE / "power-law-fits.pdf"

def add_lines(ax, n_lines, **plot_kwargs):
    """Add n_lines cubic curves with y = c*x**3 scaling."""

    xmin, xmax = sorted(ax.get_xlim())
    ymin, ymax = sorted(ax.get_ylim())

    constants = np.logspace(
        np.log10(ymin / xmax**3),
        np.log10(ymax / xmin**3),
        n_lines,
    )

    # More than 2 points gives smooth curves on linear axes
    x = np.logspace(np.log10(xmin), np.log10(xmax), 200)

    for c in constants:
        ax.plot(x, c * x**3, **plot_kwargs)

    ax.set_xlim(xmin, xmax)
    ax.set_ylim(ymin, ymax)


SCALAPACK_QUANTITIES = [
    # "polarization_time",
    "wannier_time",
    "fourier_ev_time",
    "dipole_matrix_time",
    "dipole_term_time",
    "berry_term_time",
]

LABELS = {
    "polarization_time": "Polarization",
    "wannier_time": "Polarization (total)",
    "fourier_ev_time": "Fourier EV",
    "dipole_matrix_time": "Dipole matrix",
    "dipole_term_time": "Dipole term",
    "berry_term_time": "Berry term",
    "converge_time": "SCF",
}


def power_law(x, A, m):
    """Evaluate y = A x^m."""
    return A * x**m


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


def main():
    # ---------------------------------------------------------
    # Read data and fitted parameters
    # ---------------------------------------------------------
    df = pd.read_csv(DATA_FILE)

    if df.empty:
        raise RuntimeError(f"No data found in {DATA_FILE}")

    with FIT_FILE.open() as f:
        fits = json.load(f)

    # ---------------------------------------------------------
    # Two-node calculations only
    # ---------------------------------------------------------
    df = df[df["nodes"] == 2].copy()

    if df.empty:
        raise RuntimeError("No two-node data found")

    scalapack = df[df["method"] == "scalapack"].copy()

    # ---------------------------------------------------------
    # Plot
    # ---------------------------------------------------------
    fig, ax = plt.subplots()

    # ScaLAPACK quantities
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

        A = fits[quantity]["A"]
        m = fits[quantity]["m"]

        # Plot data first and grab its automatically assigned color.
        points = ax.plot(
            x,
            y,
            "o",
            # label=LABELS.get(quantity, quantity),
        )[0]

        color = points.get_color()

        # Smooth fitted curve.
        x_fit = np.logspace(
            np.log10(x.min()),
            np.log10(x.max()),
            300,
        )

        ax.plot(
            x_fit,
            power_law(x_fit, A, m),
            "-" if quantity == "wannier_time" else "--",
            color=color,
            label=LABELS[quantity],
        )

    # ---------------------------------------------------------
    # Charge-density convergence
    # ---------------------------------------------------------
    if (
        "converge_time" in df.columns
        and "converge_time" in fits
    ):

        converge = (
            df[["atoms", "converge_time"]]
            .dropna()
            .drop_duplicates(subset=["atoms"])
            .sort_values("atoms")
        )

        x, y = clean_data(
            converge,
            "converge_time",
        )

        if len(x) > 0:

            A = fits["converge_time"]["A"]
            m = fits["converge_time"]["m"]

            points = ax.plot(
                x,
                y,
                "o",
                # label=LABELS["converge_time"],
            )[0]

            color = points.get_color()

            x_fit = np.logspace(
                np.log10(x.min()),
                np.log10(x.max()),
                300,
            )

            ax.plot(
                x_fit,
                power_law(x_fit, A, m),
                "-",
                color=color,
                label=LABELS["converge_time"],
            )

    # ---------------------------------------------------------
    # Formatting
    # ---------------------------------------------------------
    ax.set_xscale("log")
    ax.set_yscale("log")

    ax.set_xlabel("Number of atoms")
    ax.set_ylabel("Time")
    ax.set_title(
        r"Two-node atom scaling: "
        r"$y = A x^m$"
    )

    # ax.grid(
    #     True,
    #     which="both",
    #     alpha=0.25,
    # )

    ax.legend(ncol=1)
    
    # Ideal scaling guides
    add_lines(
        ax,
        n_lines=20,
        color="gray",
        alpha=0.5,
        linewidth=0.5,
        linestyle="--",
    )

    print(f"Saved {OUTPUT_FILE}")
    plt.tight_layout()
    plt.savefig(
        OUTPUT_FILE,
        bbox_inches="tight",
    )


if __name__ == "__main__":
    main()