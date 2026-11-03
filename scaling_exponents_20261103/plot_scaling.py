#!/usr/bin/env python3
"""Plot t_dipole - t_SCF and its log-log fitted line for every series.

Run after build_dataset.py:
    python3 plot_scaling.py
"""

import csv
import math
from collections import defaultdict
from pathlib import Path

import matplotlib.pyplot as plt


ROOT = Path(__file__).resolve().parent


def fit_loglog(points):
    x = [math.log(point["cores"]) for point in points]
    y = [math.log(point["polarization_time_s"]) for point in points]
    xm, ym = sum(x) / len(x), sum(y) / len(y)
    alpha = sum((a - xm) * (b - ym) for a, b in zip(x, y)) / sum((a - xm) ** 2 for a in x)
    intercept = ym - alpha * xm
    return alpha, intercept


def main():
    groups = defaultdict(list)
    with (ROOT / "timing_data.csv").open(newline="") as handle:
        for row in csv.DictReader(handle):
            row["cores"] = int(row["cores"])
            row["polarization_time_s"] = float(row["polarization_time_s"])
            groups[row["series_id"]].append(row)

    figure, axes = plt.subplots(2, 4, figsize=(16, 7), constrained_layout=True)
    for axis, (_, points) in zip(axes.flat, sorted(groups.items())):
        points.sort(key=lambda row: row["cores"])
        alpha, intercept = fit_loglog(points)
        x = [row["cores"] for row in points]
        y = [row["polarization_time_s"] for row in points]
        fit_y = [math.exp(intercept) * value**alpha for value in x]
        axis.loglog(x, y, "o", label="dipole − SCF")
        axis.loglog(x, fit_y, "-", label=fr"fit: $p={abs(alpha):.3f}$")
        axis.set_title(
            f"{points[0]['supercell']} {points[0]['functional']}\n"
            f"polarization {points[0]['polarization_grid']}"
        )
        axis.set_xlabel("MPI ranks")
        axis.set_ylabel("polarization time (s)")
        axis.grid(True, which="both", alpha=0.25)
        axis.legend(fontsize=8)
    figure.savefig(ROOT / "scaling_loglog.png", dpi=200)


if __name__ == "__main__":
    main()
