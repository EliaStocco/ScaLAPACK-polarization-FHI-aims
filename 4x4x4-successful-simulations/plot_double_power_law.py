#!/usr/bin/env python3
"""Plot the dipole-minus-SCF CPU time for the 4x4x4 calculations.

The presentation follows ``performance-water/final-alltoall-load/plot.py``:
logarithmic axes, power-law fits, and inverse-core-count guide lines.  FHI-aims
reports both ``max(cpu_time)`` and ``wall_clock(cpu1)`` in its final timing
table; this analysis uses the former, consistently with the reference plot.
"""

from __future__ import annotations

import csv
import json
import re
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.ticker import FixedLocator, NullLocator, ScalarFormatter
from scipy.optimize import least_squares


HERE = Path(__file__).resolve().parent
RESULTS = HERE / "4x4x4"
STYLE = HERE.parent / "style.mplstyle"
FUNCTIONALS = ["LDA", "HSE06"]
XTICKS = [128, 256, 512, 1080, 2048]
XLIM = (110, 2400)
EXCLUDED_CORE_COUNTS = {768, 900, 1023, 1024}
FIT_EXCLUDED_CORE_COUNTS = {2048}
TIME_PATTERN = re.compile(r"\| Total time\s*:\s*([0-9.]+)\s*s")


def parse_cpu_time(outfile: Path) -> float:
    """Read max(cpu_time) from the final FHI-aims timing table."""

    matches = TIME_PATTERN.findall(outfile.read_text(errors="replace"))
    if not matches:
        raise ValueError(f"No total CPU time found in {outfile}")
    return float(matches[-1])


def read_calculation(functional: str, calculation: str) -> dict[int, float]:
    """Return CPU times indexed by the MPI ranks encoded in each filename."""

    calculation_dir = RESULTS / f"{calculation}-{functional}"
    timings = {}
    for outfile in calculation_dir.glob("n=*/aims.n=*.out"):
        ncores = int(outfile.stem.removeprefix("aims.n="))
        if ncores in timings:
            raise ValueError(
                f"Duplicate {calculation} result for {functional} at {ncores} ranks"
            )
        timings[ncores] = parse_cpu_time(outfile)
    return timings


def collect_data() -> list[dict[str, object]]:
    """Pair successful dipole and SCF runs and calculate their difference."""

    records = []
    for functional in FUNCTIONALS:
        scf = read_calculation(functional, "scf")
        dipole = read_calculation(functional, "dipole")
        for dipole_ncores, dipole_time in sorted(dipole.items()):
            if dipole_ncores in EXCLUDED_CORE_COUNTS:
                continue
            scf_ncores = dipole_ncores
            if scf_ncores not in scf:
                raise ValueError(
                    f"No SCF result to pair with {functional} dipole result "
                    f"at {dipole_ncores} ranks"
                )
            scf_time = scf[scf_ncores]
            polarization_time = dipole_time - scf_time
            if polarization_time <= 0:
                raise ValueError(
                    f"Non-positive dipole-minus-SCF time for {functional} "
                    f"at {dipole_ncores} ranks"
                )
            records.append(
                {
                    "functional": functional,
                    "ncores": dipole_ncores,
                    "scf_ncores": scf_ncores,
                    "scf_time_s": scf_time,
                    "dipole_time_s": dipole_time,
                    "polarization_time_s": polarization_time,
                }
            )
    return records


def double_power_law(
    ncores: np.ndarray, prefactor_a: float, exponent_m: float,
    prefactor_b: float, exponent_n: float,
) -> np.ndarray:
    """Evaluate ``A * ncores**m + B * ncores**n``."""

    return (
        prefactor_a * ncores**exponent_m
        + prefactor_b * ncores**exponent_n
    )


def fit_double_power_law(records: list[dict[str, object]]) -> dict[str, float]:
    """Fit two positive, non-increasing power laws in log-residual space."""

    x = np.asarray([row["ncores"] for row in records], dtype=float)
    y = np.asarray([row["polarization_time_s"] for row in records], dtype=float)

    # Optimize log(A) and log(B) so both prefactors remain positive.  Restrict
    # both exponents to non-positive values, as expected for strong scaling.
    def residual(parameters: np.ndarray) -> np.ndarray:
        log_a, exponent_m, log_b, exponent_n = parameters
        predicted = double_power_law(
            x, np.exp(log_a), exponent_m, np.exp(log_b), exponent_n
        )
        return np.log(predicted) - np.log(y)

    center_x = np.exp(np.mean(np.log(x)))
    center_y = np.exp(np.mean(np.log(y)))
    initial_exponents = (-3.0, -2.0, -1.0, -0.5, -0.1)
    best_fit = None
    best_residual_sum = np.inf
    for exponent_m in initial_exponents:
        for exponent_n in initial_exponents:
            if exponent_m == exponent_n:
                continue
            initial = np.array(
                [
                    np.log(center_y / 2) - exponent_m * np.log(center_x),
                    exponent_m,
                    np.log(center_y / 2) - exponent_n * np.log(center_x),
                    exponent_n,
                ]
            )
            candidate = least_squares(
                residual,
                initial,
                bounds=([-40.0, -5.0, -40.0, -5.0], [40.0, 0.0, 40.0, 0.0]),
                max_nfev=20_000,
            )
            residual_sum = float(np.sum(candidate.fun**2))
            if candidate.success and residual_sum < best_residual_sum:
                best_fit = candidate.x
                best_residual_sum = residual_sum

    if best_fit is None:
        raise RuntimeError("The two-power-law fit did not converge")

    prefactor_a = float(np.exp(best_fit[0]))
    exponent_m = float(best_fit[1])
    prefactor_b = float(np.exp(best_fit[2]))
    exponent_n = float(best_fit[3])
    # The two terms are interchangeable.  Store the steeper exponent first so
    # repeated runs have a stable, easy-to-compare representation.
    if exponent_m > exponent_n:
        prefactor_a, prefactor_b = prefactor_b, prefactor_a
        exponent_m, exponent_n = exponent_n, exponent_m
    if abs(exponent_n) < 1e-10:
        exponent_n = 0.0

    return {
        "A": prefactor_a,
        "m": exponent_m,
        "B": prefactor_b,
        "n": exponent_n,
        "log_residual_sum_squares": best_residual_sum,
    }


def write_analysis(records: list[dict[str, object]]) -> dict[str, dict[str, float]]:
    """Write the plotted values and fitted parameters beside this script."""

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
        fits[functional] = fit_double_power_law(subset)

    with (HERE / "fit-double-power-law.json").open("w") as handle:
        json.dump(
            {
                "formula": "polarization_time_s = A * ncores**m + B * ncores**n",
                "fit_selection": "all extracted points except 2048 cores",
                "objective": "least squares of logarithmic residuals",
                "constraints": "A > 0, B > 0, -5 <= m <= 0, -5 <= n <= 0",
                "warning": (
                    "HSE06 has only three fitted points, so its four-parameter "
                    "model is underdetermined and not unique."
                ),
                "fits": fits,
            },
            handle,
            indent=2,
        )
        handle.write("\n")
    return fits


def add_inverse_lines(axis: plt.Axes, count: int = 14) -> None:
    """Draw log-spaced guides for ideal inverse-core-count scaling."""

    xmin, xmax = axis.get_xlim()
    ymin, ymax = axis.get_ylim()
    constants = np.logspace(np.log10(xmin * ymin), np.log10(xmax * ymax), count)
    x = np.array([xmin, xmax])
    for constant in constants:
        axis.plot(
            x,
            constant / x,
            color="0.65",
            alpha=0.45,
            linewidth=0.45,
            linestyle="--",
            zorder=0,
        )
    axis.set_xlim(xmin, xmax)
    axis.set_ylim(ymin, ymax)


def make_plot(
    records: list[dict[str, object]], fits: dict[str, dict[str, float]]
) -> None:
    """Create one scaling panel per functional."""

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

        axis.scatter(xdata, ydata, marker="o", color="#1f77b4", zorder=3)
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
        parameters = fits[functional]
        axis.plot(
            xfit,
            double_power_law(
                xfit,
                parameters["A"],
                parameters["m"],
                parameters["B"],
                parameters["n"],
            ),
            color="#1f77b4",
            linestyle="--",
            alpha=0.8,
        )
        axis.text(
            0.96,
            0.94,
            rf"$m={parameters['m']:.2f},\ n={parameters['n']:.2f}$",
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
    output = HERE / "BaTiO3.4x4x4.double-power-law.pdf"
    figure.savefig(output, bbox_inches="tight")
    plt.close(figure)
    print(f"Wrote {len(records)} paired timing records to {HERE / 'analysis-dataframe.csv'}")
    print(f"Wrote two-power-law fits to {HERE / 'fit-double-power-law.json'}")
    print(f"Wrote {output}")


def main() -> None:
    records = collect_data()
    fits = write_analysis(records)
    make_plot(records, fits)


if __name__ == "__main__":
    main()
