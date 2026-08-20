#!/usr/bin/env python3

"""Fit y = A x^m to the two-node atom-scaling timings."""

import json
from pathlib import Path

import numpy as np
import pandas as pd


BASE = Path(__file__).resolve().parent
DATA_FILE = BASE / "dataframe.csv"
OUTPUT_FILE = BASE / "power-law-fits.json"


SCALAPACK_QUANTITIES = [
    "polarization_time",
    "wannier_time",
    "fourier_ev_time",
    "dipole_matrix_time",
    "dipole_term_time",
    "berry_term_time",
]


def fit_power_law(x, y):
    """Fit y = A x^m in log-log space."""

    logx = np.log(x)
    logy = np.log(y)

    m, logA = np.polyfit(logx, logy, 1)
    A = np.exp(logA)

    return A, m


def do_fit(subset, quantity):
    """Fit one quantity and return the fit parameters."""

    subset = subset[["atoms", quantity]].dropna()

    subset = subset[
        (subset["atoms"] > 0)
        & (subset[quantity] > 0)
    ]

    if len(subset) < 2:
        raise ValueError(
            f"not enough valid points to fit {quantity}"
        )

    x = subset["atoms"].to_numpy(dtype=float)
    y = subset[quantity].to_numpy(dtype=float)

    A, m = fit_power_law(x, y)

    return {
        "A": float(A),
        "m": float(m),
        "n_points": int(len(subset)),
        "min_atoms": int(x.min()),
        "max_atoms": int(x.max()),
    }


def main():
    df = pd.read_csv(DATA_FILE)

    if df.empty:
        raise RuntimeError(f"No data found in {DATA_FILE}")

    if "nodes" not in df.columns:
        raise ValueError("Missing column: nodes")

    # ---------------------------------------------------------
    # Use only the two-node calculations.
    # ---------------------------------------------------------
    df = df[df["nodes"] == 2].copy()

    if df.empty:
        raise RuntimeError("No two-node data found")

    results = {}


    # ---------------------------------------------------------
    # ScaLAPACK polarization/component timings
    # ---------------------------------------------------------
    scalapack = df[df["method"] == "scalapack"].copy()

    if scalapack.empty:
        raise RuntimeError("No two-node ScaLAPACK data found")

    for quantity in SCALAPACK_QUANTITIES:

        if quantity not in scalapack.columns:
            print(f"[WARN] Missing column: {quantity}")
            continue

        try:
            result = do_fit(
                scalapack,
                quantity,
            )
        except ValueError as error:
            print(f"[WARN] {error}")
            continue

        results[quantity] = result

        print(
            f"{quantity:20s}: "
            f"y = {result['A']:.6e} x^{result['m']:.6f} "
            f"({result['n_points']} points)"
        )


    # ---------------------------------------------------------
    # Charge-density convergence timing
    #
    # converge_time is independent of LAPACK/ScaLAPACK and is
    # therefore duplicated in the dataframe. Keep only one
    # value for each atom count before fitting.
    # ---------------------------------------------------------
    if "converge_time" not in df.columns:
        print("[WARN] Missing column: converge_time")

    else:
        converge = (
            df[["atoms", "converge_time"]]
            .dropna()
            .drop_duplicates(subset=["atoms"])
            .sort_values("atoms")
        )

        try:
            result = do_fit(
                converge,
                "converge_time",
            )
        except ValueError as error:
            print(f"[WARN] {error}")

        else:
            results["converge_time"] = result

            print(
                f"{'converge_time':20s}: "
                f"y = {result['A']:.6e} x^{result['m']:.6f} "
                f"({result['n_points']} points)"
            )


    # ---------------------------------------------------------
    # Write JSON
    # ---------------------------------------------------------
    with OUTPUT_FILE.open("w") as f:
        json.dump(
            results,
            f,
            indent=4,
        )

    print(f"\nSaved {OUTPUT_FILE}")


if __name__ == "__main__":
    main()