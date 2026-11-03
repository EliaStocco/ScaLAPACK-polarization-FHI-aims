#!/usr/bin/env python3
"""Plot log--log scaling of FHI-aims polarization components.

Run after build_dataset.py:
    python3 plot_component_scaling.py
"""

import csv
import math
from collections import defaultdict
from pathlib import Path

import matplotlib.pyplot as plt


ROOT = Path(__file__).resolve().parent
COMPONENTS = {
    "fourier_interpolation": "Fourier interpolation",
    "dipole_matrix": "Dipole-matrix construction",
    "berry_term": "Berry term",
    "dipole_term": "Dipole term",
}


def fit_loglog(points, key):
    x = [math.log(point["cores"]) for point in points]
    y = [math.log(point[key]) for point in points]
    xm, ym = sum(x) / len(x), sum(y) / len(y)
    alpha = sum((a - xm) * (b - ym) for a, b in zip(x, y)) / sum(
        (a - xm) ** 2 for a in x
    )
    return alpha, ym - alpha * xm


def main():
    groups = defaultdict(list)
    with (ROOT / "timing_data.csv").open(newline="") as handle:
        for row in csv.DictReader(handle):
            row["cores"] = int(row["cores"])
            for component in COMPONENTS:
                row[f"{component}_time_s"] = float(row[f"{component}_time_s"])
            groups[row["series_id"]].append(row)

    figure, axes = plt.subplots(2, 4, figsize=(16, 7), constrained_layout=True)
    for axis, (_, points) in zip(axes.flat, sorted(groups.items())):
        points.sort(key=lambda row: row["cores"])
        for component, label in COMPONENTS.items():
            key = f"{component}_time_s"
            usable = [row for row in points if row[key] > 0.0]
            if len(usable) < 3:
                continue
            alpha, intercept = fit_loglog(usable, key)
            x = [row["cores"] for row in usable]
            y = [row[key] for row in usable]
            fit_y = [math.exp(intercept) * value**alpha for value in x]
            axis.loglog(x, y, "o")
            axis.loglog(x, fit_y, "-", label=fr"{label}: $p={abs(alpha):.3f}$")
        axis.set_title(
            f"{points[0]['supercell']} {points[0]['functional']}\\n"
            f"polarization {points[0]['polarization_grid']}"
        )
        axis.set_xlabel("MPI ranks")
        axis.set_ylabel("component time (s)")
        axis.grid(True, which="both", alpha=0.25)
        axis.legend(fontsize=7)
    figure.savefig(ROOT / "component_scaling_loglog.png", dpi=200)


if __name__ == "__main__":
    main()
