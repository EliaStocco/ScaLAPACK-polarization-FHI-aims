#!/usr/bin/env python3
"""Plot water polarization timing components for every scaling series.

Each PDF contains total SCF and dipole-run timings plus their difference,
broken down into polarization components.  Run ``extract.py`` first to
refresh ``dataframe.csv``.
"""

from __future__ import annotations

import csv
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.ticker import FixedLocator, NullLocator, ScalarFormatter
import numpy as np


HERE = Path(__file__).resolve().parent
STYLE_FILE = HERE.parent.parent / "style.mplstyle"
DATA_FILE = HERE / "dataframe.csv"
OUTPUT_DIRECTORY = HERE / "component-plots"
SCALABILITY_FILE = HERE / "component-scalability.csv"
# Match fit-dataframe.py: do not use the HSE06 2048-core timings in plots or
# component power-law fits, while preserving them in the raw dataframe.
EXCLUDED_SERIES_POINTS = {("HSE06", 2048)}
FUNCTIONAL_ORDER = {"revPBE": 0, "HSE06": 1, "revPBE0": 2}
CORE_COUNTS = [128, 256, 512, 1024, 2048]
CORE_XLIM = (128, 2048)

COMPONENTS = (
    ("scf_time_s", "SCF (total)", "#0173b2", "o", "-"),
    ("polarization_time_s", "Polarization (total)", "#de8f05", "s", "-"),
    ("fourier_ev_time_s", "Fourier interpolation", "#d55e00", "^", "--"),
    ("dipole_matrix_time_s", "Dipole matrix", "#cc78bc", "D", "--"),
    ("dipole_term_time_s", "Dipole term", "#ca9161", "v", "--"),
    ("berry_term_time_s", "Berry term", "#7a7a7a", "P", "--"),
    ("extra_time_s", "Extra", "#029e73", "X", "--"),
)


def as_float(value: str | None) -> float | None:
    return float(value) if value not in (None, "") else None


def load_series() -> dict[tuple[str, int], list[dict[str, float]]]:
    """Pair SCF and dipole runs and calculate the end-to-end residual."""

    with DATA_FILE.open(newline="") as handle:
        raw_rows = list(csv.DictReader(handle))

    runs: dict[tuple[str, int, int], dict[str, dict[str, str]]] = {}
    for row in raw_rows:
        key = (row["functional"], int(row["molecules"]), int(row["ncores"]))
        runs.setdefault(key, {})[row["calculation"]] = row

    series: dict[tuple[str, int], list[dict[str, float]]] = {}
    for (functional, molecules, ncores), calculations in sorted(runs.items()):
        if (functional, ncores) in EXCLUDED_SERIES_POINTS:
            continue
        if not {"scf", "dipole"} <= calculations.keys():
            continue
        scf = calculations["scf"]
        dipole = calculations["dipole"]
        scf_time = float(scf["time_s"])
        dipole_time = float(dipole["time_s"])
        polarization_time = dipole_time - scf_time
        wannier_time = as_float(dipole["wannier_time_s"])
        if polarization_time <= 0 or wannier_time is None:
            continue

        row = {
            "ncores": float(ncores),
            "scf_time_s": scf_time,
            "dipole_time_s": dipole_time,
            "polarization_time_s": polarization_time,
            # As in scaling-right.pdf, plot the residual magnitude on the
            # logarithmic axis because it can be signed.
            "extra_time_s": abs(polarization_time - wannier_time),
        }
        for name, *_ in COMPONENTS[2:-1]:
            row[name] = as_float(dipole[name])
        series.setdefault((functional, molecules), []).append(row)

    for rows in series.values():
        rows.sort(key=lambda row: row["ncores"])
    return series


def add_inverse_scaling_guides(axis: plt.Axes, count: int = 12) -> None:
    """Draw log-spaced guides with the ideal strong-scaling exponent ``m=-1``."""

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


def configure_axis(axis: plt.Axes) -> None:
    """Apply the common core-count scale and ideal-scaling guides."""

    axis.set_xscale("log", base=2)
    axis.set_yscale("log")
    axis.set_xlim(*CORE_XLIM)
    axis.xaxis.set_major_locator(FixedLocator(CORE_COUNTS))
    axis.xaxis.set_major_formatter(ScalarFormatter())
    axis.xaxis.set_minor_locator(NullLocator())
    add_inverse_scaling_guides(axis)


def fit_power_law(rows: list[dict[str, float]], name: str) -> tuple[float, float]:
    """Fit one timing series to ``time = A * ncores**m`` in log space."""

    ncores = np.array([row["ncores"] for row in rows])
    times = np.array([row[name] for row in rows])
    exponent, intercept = np.polyfit(np.log10(ncores), np.log10(times), 1)
    return 10**intercept, exponent


def plot_total(axis: plt.Axes, rows: list[dict[str, float]], name: str, title: str) -> None:
    """Plot one end-to-end timing series."""

    color = "#0173b2" if name == "scf_time_s" else "#de8f05"
    marker = "o" if name == "scf_time_s" else "s"
    axis.plot(
        [row["ncores"] for row in rows],
        [row[name] for row in rows],
        color=color,
        marker=marker,
        label=title,
    )
    prefactor, exponent = fit_power_law(rows, name)
    ncores = np.logspace(
        np.log10(rows[0]["ncores"]), np.log10(rows[-1]["ncores"]), 300
    )
    axis.plot(
        ncores,
        prefactor * ncores**exponent,
        color=color,
        linestyle="--",
        alpha=0.8,
    )
    configure_axis(axis)
    axis.set_title(title)
    axis.set_ylabel("CPU time (s)")
    axis.text(
        0.04,
        0.06,
        f"$A={prefactor:.2e}$\n$m={exponent:.2f}$",
        color=color,
        transform=axis.transAxes,
        va="bottom",
    )


def plot_series(functional: str, molecules: int, rows: list[dict[str, float]]) -> Path:
    """Create SCF, dipole, and component-breakdown panels for one series."""

    figure = plt.figure(figsize=(10, 9), constrained_layout=True)
    grid = figure.add_gridspec(2, 2)
    scf_axis = figure.add_subplot(grid[0, 0])
    dipole_axis = figure.add_subplot(grid[0, 1], sharex=scf_axis)
    difference_axis = figure.add_subplot(grid[1, :], sharex=scf_axis)

    plot_total(scf_axis, rows, "scf_time_s", "SCF")
    plot_total(dipole_axis, rows, "dipole_time_s", "Dipole calculation")

    for name, label, color, marker, linestyle in COMPONENTS[1:]:
        subset = [row for row in rows if row.get(name) is not None and row[name] > 0]
        difference_axis.plot(
            [row["ncores"] for row in subset],
            [row[name] for row in subset],
            color=color,
            marker=marker,
            linestyle=linestyle,
            label=label,
        )
    configure_axis(difference_axis)
    difference_axis.set_title("Polarization overhead (dipole − SCF)")
    difference_axis.set_ylabel("CPU time (s)")
    difference_axis.set_xlabel("n. cores")
    difference_axis.legend(loc="upper right", ncol=2)

    scf_axis.tick_params(labelbottom=False)
    dipole_axis.tick_params(labelbottom=False)
    figure.suptitle(f"{functional}, {molecules} water molecules")

    output = OUTPUT_DIRECTORY / f"components-{functional}-m{molecules}.pdf"
    figure.savefig(output, bbox_inches="tight")
    plt.close(figure)
    return output


def scaling_behavior(exponent: float) -> str:
    """Classify the core-count exponent relative to ideal inverse scaling."""

    if exponent <= -1.15:
        return "faster than ideal inverse"
    if exponent <= -0.85:
        return "near ideal inverse"
    if exponent < -0.15:
        return "slower than ideal inverse"
    if exponent < 0.15:
        return "approximately core-count independent"
    return "increases with core count"


def write_scalability_csv(series: dict[tuple[str, int], list[dict[str, float]]]) -> None:
    """Fit every component to ``time = A * ncores**m`` and save the summary."""

    summary = []
    for (functional, molecules), rows in series.items():
        for name, label, *_ in COMPONENTS:
            subset = [row for row in rows if row.get(name) is not None and row[name] > 0]
            if len(subset) < 3:
                continue

            ncores = np.array([row["ncores"] for row in subset])
            times = np.array([row[name] for row in subset])
            log_ncores = np.log10(ncores)
            log_times = np.log10(times)
            (exponent, intercept), covariance = np.polyfit(
                log_ncores, log_times, 1, cov=True
            )
            fitted = exponent * log_ncores + intercept
            residual_sum = np.sum((log_times - fitted) ** 2)
            total_sum = np.sum((log_times - np.mean(log_times)) ** 2)
            r_squared = 1 - residual_sum / total_sum if total_sum else 1.0

            summary.append({
                "functional": functional,
                "molecules": molecules,
                "component": name,
                "component_label": label,
                "n_points": len(subset),
                "exponent_m": exponent,
                "exponent_std_error": np.sqrt(covariance[0, 0]),
                "prefactor_A": 10**intercept,
                "log10_r_squared": r_squared,
                "deviation_from_ideal_inverse": abs(exponent + 1),
                "time_factor_per_core_doubling": 2**exponent,
                "behavior": scaling_behavior(exponent),
            })

    # Place the most non-ideal curves first so the file can be read directly.
    summary.sort(key=lambda row: row["deviation_from_ideal_inverse"], reverse=True)
    for rank, row in enumerate(summary, start=1):
        row["non_ideal_rank"] = rank

    fields = [
        "non_ideal_rank", "functional", "molecules", "component", "component_label",
        "n_points", "exponent_m", "exponent_std_error", "prefactor_A",
        "log10_r_squared", "deviation_from_ideal_inverse",
        "time_factor_per_core_doubling", "behavior",
    ]
    with SCALABILITY_FILE.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(summary)
    print(f"Wrote {SCALABILITY_FILE}")


def main() -> None:
    if STYLE_FILE.exists():
        plt.style.use(STYLE_FILE)
    OUTPUT_DIRECTORY.mkdir(exist_ok=True)

    series = load_series()
    if not series:
        raise RuntimeError(f"No paired SCF/dipole series found in {DATA_FILE}")
    write_scalability_csv(series)
    for (functional, molecules), rows in sorted(
        series.items(),
        key=lambda item: (
            FUNCTIONAL_ORDER.get(item[0][0], len(FUNCTIONAL_ORDER)),
            item[0][0],
            item[0][1],
        ),
    ):
        print(f"Wrote {plot_series(functional, molecules, rows)}")


if __name__ == "__main__":
    main()
