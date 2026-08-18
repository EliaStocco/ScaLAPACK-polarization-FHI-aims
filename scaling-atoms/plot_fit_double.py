#!/usr/bin/env python3

"""Fit and plot y = A x^m + B x^n for two-node atom-scaling timings."""

import json
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.optimize import least_squares
from plot_fit import SCALAPACK_QUANTITIES, LABELS, add_lines


BASE = Path(__file__).resolve().parent
STYLE_FILE = BASE.parent / "style.mplstyle"
plt.style.use(STYLE_FILE)
DATA_FILE = BASE / "dataframe.csv"
OUTPUT_FILE = BASE / "two-power-law-fits.pdf"
FIT_FILE = BASE / "two-power-law-fits.json"



def two_power_law(x, A, m, B, n):
    """Evaluate y = A x^m + B x^n."""
    return A * x**m + B * x**n


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


def fit_two_power_laws(x, y):
    """
    Fit

        y = A x^m + B x^n

    by minimizing residuals in log(y).

    A and B are represented internally as exp(logA) and exp(logB),
    which guarantees positive coefficients.
    """

    if len(x) < 4:
        raise ValueError(
            "at least four data points are required for a "
            "four-parameter fit"
        )

    # ---------------------------------------------------------
    # First estimate the overall scaling exponent from a
    # single power-law fit. This is used only to generate
    # sensible initial guesses for the nonlinear fit.
    # ---------------------------------------------------------
    slope, intercept = np.polyfit(
        np.log(x),
        np.log(y),
        1,
    )

    A_single = np.exp(intercept)
    m_single = slope

    # ---------------------------------------------------------
    # Residuals in log space.
    #
    # This approximately gives equal importance to fractional
    # errors across quantities spanning several orders of
    # magnitude.
    # ---------------------------------------------------------
    def residuals(params):
        logA, m, logB, n = params

        A = np.exp(logA)
        B = np.exp(logB)

        y_model = two_power_law(
            x,
            A,
            m,
            B,
            n,
        )

        return np.log(y_model) - np.log(y)

    # ---------------------------------------------------------
    # Because this is a nonlinear four-parameter problem, use
    # several starting guesses and keep the best solution.
    # ---------------------------------------------------------
    guesses = []

    exponent_offsets = [
        (-2.0, 2.0),
        (-1.5, 1.5),
        (-1.0, 1.0),
        (-0.5, 0.5),
        (-2.0, 0.5),
        (-0.5, 2.0),
    ]

    for dm, dn in exponent_offsets:
        guesses.append(
            [
                np.log(A_single / 2.0),
                m_single + dm,
                np.log(A_single / 2.0),
                m_single + dn,
            ]
        )

    best_result = None
    best_cost = np.inf

    for guess in guesses:

        result = least_squares(
            residuals,
            guess,
            max_nfev=100000,
        )

        if result.cost < best_cost:
            best_cost = result.cost
            best_result = result

    if best_result is None or not best_result.success:
        raise RuntimeError("two-power-law fit failed")

    logA, m, logB, n = best_result.x

    A = np.exp(logA)
    B = np.exp(logB)

    # ---------------------------------------------------------
    # The two terms are mathematically interchangeable:
    #
    # A x^m + B x^n = B x^n + A x^m
    #
    # Sort them so that m <= n, making results easier to read
    # and compare.
    # ---------------------------------------------------------
    if m > n:
        A, B = B, A
        m, n = n, m

    return A, m, B, n


def fit_and_plot(
    ax,
    df,
    quantity,
    results,
):
    """Fit one quantity and add data + fitted curve to the plot."""

    x, y = clean_data(
        df,
        quantity,
    )

    if len(x) < 4:
        print(
            f"[WARN] Not enough points for {quantity}: "
            f"{len(x)}"
        )
        return

    try:
        A, m, B, n = fit_two_power_laws(
            x,
            y,
        )
    except (ValueError, RuntimeError) as error:
        print(f"[WARN] {quantity}: {error}")
        return

    # Save parameters.
    results[quantity] = {
        "A": float(A),
        "m": float(m),
        "B": float(B),
        "n": float(n),
        "n_points": int(len(x)),
        "min_atoms": int(x.min()),
        "max_atoms": int(x.max()),
    }

    print(
        f"{quantity:20s}: "
        f"y = {A:.6e} x^{m:.6f} "
        f"+ {B:.6e} x^{n:.6f} "
        f"({len(x)} points)"
    )

    # ---------------------------------------------------------
    # Plot data.
    # ---------------------------------------------------------
    label = LABELS.get(
        quantity,
        quantity,
    )

    points = ax.plot(
        x,
        y,
        "o",
    )[0]

    color = points.get_color()

    # ---------------------------------------------------------
    # Plot smooth fitted curve.
    # ---------------------------------------------------------
    x_fit = np.logspace(
        np.log10(x.min()),
        np.log10(x.max()),
        500,
    )

    y_fit = two_power_law(
        x_fit,
        A,
        m,
        B,
        n,
    )

    ax.plot(
        x_fit,
        y_fit,
        "-" if quantity in ["wannier_time","converge_time"] else "--",
        color=color,
        label=label
    )


def main():

    # ---------------------------------------------------------
    # Read dataframe
    # ---------------------------------------------------------
    df = pd.read_csv(DATA_FILE)

    if df.empty:
        raise RuntimeError(
            f"No data found in {DATA_FILE}"
        )

    if "nodes" not in df.columns:
        raise ValueError(
            "Missing column: nodes"
        )

    # ---------------------------------------------------------
    # Two-node calculations only
    # ---------------------------------------------------------
    df = df[
        df["nodes"] == 2
    ].copy()

    if df.empty:
        raise RuntimeError(
            "No two-node data found"
        )

    # ---------------------------------------------------------
    # ScaLAPACK data
    # ---------------------------------------------------------
    scalapack = df[
        df["method"] == "scalapack"
    ].copy()

    if scalapack.empty:
        raise RuntimeError(
            "No two-node ScaLAPACK data found"
        )

    # ---------------------------------------------------------
    # Figure
    # ---------------------------------------------------------
    fig, ax = plt.subplots()

    results = {}

    # ---------------------------------------------------------
    # ScaLAPACK quantities
    # ---------------------------------------------------------
    for quantity in SCALAPACK_QUANTITIES:

        if quantity not in scalapack.columns:
            print(
                f"[WARN] Missing column: {quantity}"
            )
            continue

        fit_and_plot(
            ax,
            scalapack,
            quantity,
            results,
        )

    # ---------------------------------------------------------
    # Charge-density convergence
    #
    # It is duplicated between LAPACK/ScaLAPACK, so keep one
    # value per atom count.
    # ---------------------------------------------------------
    if "converge_time" not in df.columns:

        print(
            "[WARN] Missing column: converge_time"
        )

    else:

        converge = (
            df[["atoms", "converge_time"]]
            .dropna()
            .drop_duplicates(subset=["atoms"])
            .sort_values("atoms")
        )

        fit_and_plot(
            ax,
            converge,
            "converge_time",
            results,
        )

    # ---------------------------------------------------------
    # Formatting
    # ---------------------------------------------------------
    ax.set_xscale("log")
    ax.set_yscale("log")

    ax.set_xlabel(
        "Number of atoms"
    )

    ax.set_ylabel(
        "Time"
    )

    ax.set_title(
        r"Two-node atom scaling: "
        r"$y = A x^m + B x^n$"
    )

    # ax.grid(
    #     True,
    #     which="both",
    #     alpha=0.25,
    # )

    ax.legend(
        fontsize=8,
    )

    fig.tight_layout()

    # ---------------------------------------------------------
    # Save figure
    # ---------------------------------------------------------
    fig.savefig(
        OUTPUT_FILE,
        dpi=300,
        bbox_inches="tight",
    )

    print(
        f"\nSaved {OUTPUT_FILE}"
    )

    # ---------------------------------------------------------
    # Save fit parameters
    # ---------------------------------------------------------
    with FIT_FILE.open("w") as f:
        json.dump(
            results,
            f,
            indent=4,
        )

    print(
        f"Saved {FIT_FILE}"
    )

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