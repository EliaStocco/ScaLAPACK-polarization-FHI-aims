#!/usr/bin/env python3
"""Analyze BaTiO3 polarization timing components versus core count.

The script reads the raw FHI-aims outputs directly and writes a paired timing
table, a power-law summary, and one component-breakdown PDF per supercell.
It uses the first timing value (max CPU time), consistently with the existing
BaTiO3 scaling plot and its ``CPU time (s)`` axis.
"""

from __future__ import annotations

import csv
import re
from collections import defaultdict
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.ticker import FixedLocator, NullLocator, ScalarFormatter
import numpy as np


HERE = Path(__file__).resolve().parent
STYLE_FILE = HERE.parent / "style.mplstyle"
COMPONENT_DATA_FILE = HERE / "component-dataframe.csv"
SCALABILITY_FILE = HERE / "component-scalability.csv"
PLOT_DIRECTORY = HERE / "component-plots"

TOTAL_TIME_PATTERN = re.compile(
    r"^\s*\|\s*Total time\s*:\s*([\d.eE+-]+)\s*s", re.MULTILINE
)
COMPONENT_PATTERNS = {
    "wannier_time_s": re.compile(
        r"\|\s*Total time for Wannier Center Evolution\s*:\s*([\d.eE+-]+)\s*s"
    ),
    "fourier_ev_time_s": re.compile(
        r"\|\s*Total Time for Fourier interpolated EV solution\s*:\s*([\d.eE+-]+)"
    ),
    "dipole_matrix_time_s": re.compile(
        r"\|\s*Total Time for dipole matrix\s*:\s*([\d.eE+-]+)"
    ),
    "dipole_term_time_s": re.compile(
        r"\|\s*Total Time for dipole term\s*:\s*([\d.eE+-]+)"
    ),
    "berry_term_time_s": re.compile(
        r"\|\s*Total Time for berry term\s*:\s*([\d.eE+-]+)"
    ),
}
COMPONENTS = (
    ("scf_time_s", "SCF (total)", "#0173b2", "o", "-"),
    ("polarization_time_s", "Polarization (total)", "#de8f05", "s", "-"),
    ("fourier_ev_time_s", "Fourier interpolation", "#d55e00", "^", "--"),
    ("dipole_matrix_time_s", "Dipole matrix", "#cc78bc", "D", "--"),
    ("dipole_term_time_s", "Dipole term", "#ca9161", "v", "--"),
    ("berry_term_time_s", "Berry term", "#7a7a7a", "P", "--"),
    ("extra_time_s", "Extra", "#029e73", "X", "--"),
)


def parse_output(path: Path, include_components: bool) -> dict[str, float]:
    """Read total CPU time and, for dipole runs, internal component timers."""

    text = path.read_text(errors="replace")
    match = TOTAL_TIME_PATTERN.search(text)
    if match is None:
        raise ValueError(f"No total time found in {path}")

    result = {"time_s": float(match.group(1))}
    if include_components:
        for name, pattern in COMPONENT_PATTERNS.items():
            values = [float(value) for value in pattern.findall(text)]
            if not values:
                raise ValueError(f"No {name} entries found in {path}")
            # The output contains one such block per polarization direction.
            result[name] = sum(values)
    return result


def load_series() -> dict[str, list[dict[str, float]]]:
    """Pair SCF and dipole outputs with the same supercell and core count."""

    runs: dict[tuple[str, int], dict[str, dict[str, float]]] = defaultdict(dict)
    for path in HERE.glob("*x*x*/**/aims.n=*.out"):
        supercell, calculation, filename = path.relative_to(HERE).parts
        if calculation not in {"scf", "dipole"}:
            continue
        ncores = int(filename.removeprefix("aims.n=").removesuffix(".out"))
        try:
            runs[(supercell, ncores)][calculation] = parse_output(
                path, include_components=calculation == "dipole"
            )
        except ValueError as error:
            print(f"[WARN] Skipping {path.relative_to(HERE)}: {error}")

    series: dict[str, list[dict[str, float]]] = defaultdict(list)
    for (supercell, ncores), calculations in sorted(runs.items()):
        if not {"scf", "dipole"} <= calculations.keys():
            continue
        scf = calculations["scf"]
        dipole = calculations["dipole"]
        polarization_time = dipole["time_s"] - scf["time_s"]
        if polarization_time <= 0:
            print(f"[WARN] Skipping {supercell} at {ncores} cores: non-positive polarization time")
            continue

        row = {
            "supercell": supercell,
            "ncores": float(ncores),
            "scf_time_s": scf["time_s"],
            "dipole_time_s": dipole["time_s"],
            "polarization_time_s": polarization_time,
            **{name: dipole[name] for name in COMPONENT_PATTERNS},
        }
        row["extra_time_s"] = abs(row["polarization_time_s"] - row["wannier_time_s"])
        series[supercell].append(row)

    for rows in series.values():
        rows.sort(key=lambda row: row["ncores"])
    return dict(series)


def write_component_data(series: dict[str, list[dict[str, float]]]) -> None:
    fields = [
        "supercell", "ncores", "scf_time_s", "dipole_time_s", "polarization_time_s",
        *COMPONENT_PATTERNS, "extra_time_s",
    ]
    with COMPONENT_DATA_FILE.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for rows in series.values():
            writer.writerows(rows)
    print(f"Wrote {COMPONENT_DATA_FILE}")


def scaling_behavior(exponent: float) -> str:
    if exponent <= -1.15:
        return "faster than ideal inverse"
    if exponent <= -0.85:
        return "near ideal inverse"
    if exponent < -0.15:
        return "slower than ideal inverse"
    if exponent < 0.15:
        return "approximately core-count independent"
    return "increases with core count"


def write_scalability_csv(series: dict[str, list[dict[str, float]]]) -> None:
    """Fit each timing component to ``time = A * ncores**m``."""

    summary = []
    for supercell, rows in series.items():
        for name, label, *_ in COMPONENTS:
            subset = [row for row in rows if row[name] > 0]
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
            summary.append({
                "supercell": supercell,
                "component": name,
                "component_label": label,
                "n_points": len(subset),
                "exponent_m": exponent,
                "exponent_std_error": np.sqrt(covariance[0, 0]),
                "prefactor_A": 10**intercept,
                "log10_r_squared": 1 - residual_sum / total_sum if total_sum else 1.0,
                "deviation_from_ideal_inverse": abs(exponent + 1),
                "time_factor_per_core_doubling": 2**exponent,
                "behavior": scaling_behavior(exponent),
            })

    summary.sort(key=lambda row: row["deviation_from_ideal_inverse"], reverse=True)
    for rank, row in enumerate(summary, start=1):
        row["non_ideal_rank"] = rank
    fields = [
        "non_ideal_rank", "supercell", "component", "component_label", "n_points",
        "exponent_m", "exponent_std_error", "prefactor_A", "log10_r_squared",
        "deviation_from_ideal_inverse", "time_factor_per_core_doubling", "behavior",
    ]
    with SCALABILITY_FILE.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(summary)
    print(f"Wrote {SCALABILITY_FILE}")


def plot_series(supercell: str, rows: list[dict[str, float]]) -> Path:
    figure, axis = plt.subplots(figsize=(8, 3))
    for name, label, color, marker, linestyle in COMPONENTS:
        axis.plot(
            [row["ncores"] for row in rows],
            [row[name] for row in rows],
            color=color,
            marker=marker,
            linestyle=linestyle,
            label=label,
        )

    core_counts = [row["ncores"] for row in rows]
    axis.set_xscale("log", base=2)
    axis.set_yscale("log")
    axis.xaxis.set_major_locator(FixedLocator(core_counts))
    axis.xaxis.set_major_formatter(ScalarFormatter())
    axis.xaxis.set_minor_locator(NullLocator())
    axis.set_xlabel("n. cores")
    axis.set_ylabel("CPU time (s)")
    axis.set_title(f"BaTiO3, {supercell} supercell")
    legend = axis.legend(loc="upper left", bbox_to_anchor=(1.02, 1), borderaxespad=0)
    legend._legend_box.align = "left"
    figure.tight_layout()
    output = PLOT_DIRECTORY / f"components-{supercell}.pdf"
    figure.savefig(output, bbox_inches="tight")
    plt.close(figure)
    return output


def main() -> None:
    if STYLE_FILE.exists():
        plt.style.use(STYLE_FILE)
    series = load_series()
    if not series:
        raise RuntimeError("No paired BaTiO3 SCF/dipole outputs were found")
    write_component_data(series)
    write_scalability_csv(series)
    PLOT_DIRECTORY.mkdir(exist_ok=True)
    for supercell, rows in series.items():
        print(f"Wrote {plot_series(supercell, rows)}")


if __name__ == "__main__":
    main()
