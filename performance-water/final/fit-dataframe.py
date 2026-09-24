#!/usr/bin/env python3
"""Pair SCF/polarization timings and fit their scaling with core count."""

from __future__ import annotations

import json
import csv
from pathlib import Path

import numpy as np


HERE = Path(__file__).resolve().parent
# The HSE06 jobs at 2048 cores are excluded from the scaling analysis.  Keep
# their raw timings in dataframe.csv so the decision is explicit and reversible.
EXCLUDED_SERIES_POINTS = {("HSE06", 2048)}


def fit_power_law(ncores: np.ndarray, time_s: np.ndarray) -> dict[str, float]:
    """Fit ``time_s = A * ncores**m`` in log space, including uncertainties."""

    log_ncores = np.log10(ncores)
    log_time = np.log10(time_s)
    (exponent, intercept), covariance = np.polyfit(log_ncores, log_time, 1, cov=True)
    exponent_error, intercept_error = np.sqrt(np.diag(covariance))
    prefactor = 10**intercept

    return {
        "A": float(prefactor),
        "m": float(exponent),
        "log10(A)": float(intercept),
        "err-A": float(np.log(10) * prefactor * intercept_error),
        "err-m": float(exponent_error),
        "err-log10(A)": float(intercept_error),
    }


def main() -> None:
    with (HERE / "dataframe.csv").open(newline="") as handle:
        timing_data = list(csv.DictReader(handle))

    by_calculation: dict[tuple[str, int, int], dict[str, float]] = {}
    for row in timing_data:
        key = (row["functional"], int(row["molecules"]), int(row["ncores"]))
        calculations = by_calculation.setdefault(key, {})
        calculation = row["calculation"]
        if calculation in calculations:
            raise SystemExit(f"Duplicate {calculation} timing for {key}.")
        calculations[calculation] = float(row["time_s"])

    paired = []
    missing_pairs = []
    for (functional, molecules, ncores), calculations in sorted(by_calculation.items()):
        if (functional, ncores) in EXCLUDED_SERIES_POINTS:
            continue
        record = {"functional": functional, "molecules": molecules, "ncores": ncores}
        if {"scf", "dipole"} <= calculations.keys():
            record["scf"] = calculations["scf"]
            record["dipole"] = calculations["dipole"]
            record["polarization_time_s"] = record["dipole"] - record["scf"]
            paired.append(record)
        else:
            record["available_calculations"] = sorted(calculations)
            missing_pairs.append(record)

    invalid = [row for row in paired if row["polarization_time_s"] <= 0]
    if invalid:
        raise SystemExit(f"The polarization overhead must be positive: {invalid}")

    output = HERE / "analysis-dataframe.csv"
    with output.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=[
            "functional", "molecules", "ncores", "scf", "dipole", "polarization_time_s",
        ])
        writer.writeheader()
        writer.writerows(paired)

    results: dict[str, object] = {
        "formula": "polarization_time_s = A * ncores**m",
        "linear": {},
        "unpaired_calculations": missing_pairs,
    }
    fits: dict[str, dict[str, dict[str, float]]] = {}

    series: dict[tuple[str, int], list[dict[str, float]]] = {}
    for row in paired:
        series.setdefault((row["functional"], row["molecules"]), []).append(row)

    for (functional, molecules), subset in sorted(series.items()):
        subset.sort(key=lambda row: row["ncores"])
        if len(subset) < 3:
            raise SystemExit(
                f"Need at least three paired core counts for {functional}, m={molecules}."
            )
        fits.setdefault(functional, {})[str(molecules)] = fit_power_law(
            np.array([row["ncores"] for row in subset]),
            np.array([row["polarization_time_s"] for row in subset]),
        )

    results["linear"] = fits
    with (HERE / "fit.json").open("w") as handle:
        json.dump(results, handle, indent=2)
        handle.write("\n")

    print(f"Wrote {len(paired)} paired timing records to {output}")
    print(f"Wrote power-law fits to {HERE / 'fit.json'}")


if __name__ == "__main__":
    main()
