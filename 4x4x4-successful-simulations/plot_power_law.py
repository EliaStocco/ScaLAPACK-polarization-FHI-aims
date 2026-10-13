#!/usr/bin/env python3
"""Plot a single-power-law fit to the 4x4x4 dipole-minus-SCF CPU times."""

from __future__ import annotations

import csv
import json

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.ticker import FixedLocator, NullLocator, ScalarFormatter

from plot_double_power_law import (
    FUNCTIONALS,
    FIT_EXCLUDED_CORE_COUNTS,
    HERE,
    STYLE,
    XLIM,
    XTICKS,
    add_inverse_lines,
    collect_data,
)


def fit_power_law(records: list[dict[str, object]]) -> dict[str, float]:
    """Fit ``time = A * ncores**m`` by least squares in log space."""

    x = np.asarray([row["ncores"] for row in records], dtype=float)
    y = np.asarray([row["polarization_time_s"] for row in records], dtype=float)
    (exponent, intercept), covariance = np.polyfit(
        np.log10(x), np.log10(y), 1, cov=True
    )
    exponent_error, intercept_error = np.sqrt(np.diag(covariance))
    prefactor = 10**intercept
    return {
        "A": float(prefactor),
        "m": float(exponent),
        "err-A": float(np.log(10) * prefactor * intercept_error),
        "err-m": float(exponent_error),
    }


def write_analysis(records: list[dict[str, object]]) -> dict[str, dict[str, float]]:
    """Write the common extracted data and single-power-law parameters."""

    with (HERE / "analysis-dataframe.csv").open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(records[0]))
        writer.writeheader()
        writer.writerows(records)

    fits = {}
    for functional in FUNCTIONALS:
        subset = [
            row
            for row in records
            if row["functional"] == functional
            and row["ncores"] not in FIT_EXCLUDED_CORE_COUNTS
        ]
        fits[functional] = fit_power_law(subset)

    with (HERE / "fit-power-law.json").open("w") as handle:
        json.dump(
            {
                "formula": "polarization_time_s = A * ncores**m",
                "fit_selection": "all extracted points except 2048 cores",
                "objective": "least squares in log10 space",
                "fits": fits,
            },
            handle,
            indent=2,
        )
        handle.write("\n")
    return fits


def make_plot(
    records: list[dict[str, object]], fits: dict[str, dict[str, float]]
) -> None:
    """Create one single-power-law scaling panel per functional."""

    if STYLE.exists():
        plt.style.use(STYLE)

    figure, axes = plt.subplots(
        1, len(FUNCTIONALS), figsize=(6.6, 3.5), sharex=True, sharey=True
    )
    for axis, functional in zip(axes, FUNCTIONALS):
        subset = sorted(
            (row for row in records if row["functional"] == functional),
            key=lambda row: row["ncores"],
        )
        xdata = np.asarray([row["ncores"] for row in subset], dtype=float)
        ydata = np.asarray(
            [row["polarization_time_s"] for row in subset], dtype=float
        )
        parameters = fits[functional]
        fitted_xdata = np.asarray(
            [
                row["ncores"]
                for row in subset
                if row["ncores"] not in FIT_EXCLUDED_CORE_COUNTS
            ],
            dtype=float,
        )
        xfit = np.logspace(
            np.log10(fitted_xdata.min()), np.log10(fitted_xdata.max()), 300
        )

        axis.scatter(xdata, ydata, marker="o", color="#1f77b4", zorder=3)
        axis.plot(
            xfit,
            parameters["A"] * xfit ** parameters["m"],
            color="#1f77b4",
            linestyle="--",
            alpha=0.8,
        )
        axis.text(
            0.96,
            0.94,
            rf"$m={parameters['m']:.2f}$",
            color="#1f77b4",
            ha="right",
            va="top",
            transform=axis.transAxes,
        )
        axis.set_title(functional)
        axis.set_xscale("log")
        axis.set_yscale("log")
        axis.set_xlim(*XLIM)
        axis.set_xlabel("n. cores")
        axis.xaxis.set_major_locator(FixedLocator(XTICKS))
        axis.xaxis.set_major_formatter(ScalarFormatter())
        axis.xaxis.set_minor_locator(NullLocator())
        add_inverse_lines(axis)

    axes[0].set_ylabel("CPU time (s)")
    figure.suptitle(
        r"$\mathrm{BaTiO}_{3}\;4\!\times\!4\!\times\!4$ polarization scaling"
    )
    figure.tight_layout()
    output = HERE / "BaTiO3.4x4x4.power-law.pdf"
    figure.savefig(output, bbox_inches="tight")
    plt.close(figure)
    print(f"Wrote {len(records)} paired timing records to {HERE / 'analysis-dataframe.csv'}")
    print(f"Wrote power-law fits to {HERE / 'fit-power-law.json'}")
    print(f"Wrote {output}")


def main() -> None:
    records = collect_data()
    fits = write_analysis(records)
    make_plot(records, fits)


if __name__ == "__main__":
    main()
