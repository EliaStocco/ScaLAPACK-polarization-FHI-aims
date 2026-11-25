#!/usr/bin/env python3
"""Create corrected-data Figure 7 component, share, and exponent plots."""

from __future__ import annotations

import csv
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np


HERE = Path(__file__).resolve().parent
DATA = HERE / "component_timing_data.csv"
COLORS = {"total": "#0072B2", "fourier": "#E69F00", "dipole_matrix": "#009E73", "dipole": "#D55E00", "berry": "#CC79A7"}
COMPONENTS = (
    ("polarization_seconds", "Polarization (total)", "total"),
    ("fourier_seconds", "Fourier interpolation", "fourier"),
    ("dipole_matrix_seconds", "Dipole matrix", "dipole_matrix"),
    ("dipole_term_seconds", "Dipole term", "dipole"),
    ("berry_term_seconds", "Berry term", "berry"),
)
SERIES = (("4x4x4", "LDA"), ("4x4x4", "HSE06"), ("8x8x8", "LDA"), ("8x8x8", "HSE06"))


def load() -> list[dict[str, str]]:
    with DATA.open(newline="") as handle:
        return list(csv.DictReader(handle))


def fit(rows: list[dict[str, str]], column: str) -> tuple[float, float]:
    x = np.log([float(row["cores"]) for row in rows])
    y = np.log([float(row[column]) for row in rows])
    slope, intercept = np.polyfit(x, y, 1)
    return -float(slope), float(np.exp(intercept))


def grouped(rows, supercell, functional):
    return sorted([row for row in rows if row["supercell"] == supercell and row["functional"] == functional], key=lambda row: int(row["cores"]))


def component_plot(rows, output: Path) -> None:
    fig, axes = plt.subplots(2, 2, figsize=(8.5, 5.8), sharex=True, sharey=True)
    handles, labels = [], []
    all_values = [float(row[column]) for row in rows for column, _, _ in COMPONENTS]
    ylim = (min(all_values) * 0.7, max(all_values) * 1.35)
    for axis, (supercell, functional) in zip(axes.ravel(), SERIES):
        subset = grouped(rows, supercell, functional)
        x = np.array([int(row["cores"]) for row in subset], dtype=float)
        for column, label, key in COMPONENTS:
            y = np.array([float(row[column]) for row in subset])
            color = COLORS[key]
            points = axis.scatter(x, y, color=color, marker="o", edgecolor="black", linewidth=0.3, s=20)
            p, amplitude = fit(subset, column)
            fit_x = np.geomspace(x.min(), x.max(), 100)
            axis.plot(fit_x, amplitude * fit_x**(-p), color=color, linestyle="--" if key != "total" else "-", linewidth=0.8)
            if axis is axes.ravel()[0]:
                handles.append(points); labels.append(label)
        axis.set_xscale("log", base=2); axis.set_yscale("log"); axis.set_xlim(110, 2300); axis.set_ylim(*ylim)
        axis.set_xticks((128, 256, 512, 1024, 2048)); axis.get_xaxis().set_major_formatter(plt.ScalarFormatter())
        axis.text(0.04, 0.94, f"{supercell}, {functional}", transform=axis.transAxes, va="top", bbox={"facecolor": "white", "edgecolor": "black", "pad": 2})
        axis.grid(axis="y", color="0.82", linewidth=0.5)
    axes[1, 0].set_xlabel("n. cores"); axes[1, 1].set_xlabel("n. cores"); axes[0, 0].set_ylabel("CPU time (s)"); axes[1, 0].set_ylabel("CPU time (s)")
    fig.legend(handles, labels, loc="upper left", bbox_to_anchor=(0.80, 0.96), frameon=True)
    fig.subplots_adjust(left=0.09, right=0.77, bottom=0.10, top=0.94, wspace=0.16, hspace=0.16)
    fig.savefig(output, bbox_inches="tight"); plt.close(fig)


def share_plot(rows, output: Path) -> None:
    fig, axes = plt.subplots(2, 2, figsize=(8.5, 5.4), sharey=True)
    handles = []
    for index, (axis, series) in enumerate(zip(axes.ravel(), SERIES)):
        subset = grouped(rows, *series); x = np.arange(len(subset)); values = np.array([[float(row[column]) for column, _, _ in COMPONENTS[1:]] for row in subset]); values = 100 * values / values.sum(axis=1, keepdims=True)
        bottom = np.zeros(len(subset))
        for component_index, (_, label, key) in enumerate(COMPONENTS[1:]):
            bars = axis.bar(x, values[:, component_index], 1.0, bottom=bottom, color=COLORS[key], edgecolor="black", linewidth=0.35, label=label)
            if index == 0: handles.append(bars)
            bottom += values[:, component_index]
        axis.set_title(f"{series[0]}, {series[1]}"); axis.set_xticks(x, [row["cores"] for row in subset]); axis.set_ylim(0, 100); axis.set_xlim(-0.5, len(subset) - 0.5); axis.grid(axis="y", color="0.82", linewidth=0.5)
        if index % 2 == 0: axis.set_ylabel("Cost share (%)")
        if index >= 2: axis.set_xlabel("n. cores")
    fig.legend(handles, [label for _, label, _ in COMPONENTS[1:]], loc="upper left", bbox_to_anchor=(0.80, 0.96), frameon=True)
    fig.subplots_adjust(left=0.09, right=0.77, bottom=0.11, top=0.91, wspace=0.16, hspace=0.26)
    fig.savefig(output, bbox_inches="tight"); plt.close(fig)


def exponent_plot(rows, output: Path) -> None:
    fig, axes = plt.subplots(1, 4, figsize=(9.0, 3.2), sharey=True)
    x = np.arange(len(COMPONENTS))
    for axis, series in zip(axes, SERIES):
        subset = grouped(rows, *series)
        values = [fit(subset, column)[0] for column, _, _ in COMPONENTS]
        axis.bar(x, values, color=[COLORS[key] for _, _, key in COMPONENTS], edgecolor="black", linewidth=0.4)
        axis.set_title(f"{series[0]}, {series[1]}"); axis.set_xticks(x, ["total", "Fourier", "Dipole\nmatrix", "Dipole\nterm", "Berry\nterm"], rotation=35, ha="right"); axis.grid(axis="y", color="0.82", linewidth=0.5)
    axes[0].set_ylabel(r"Scalability exponent $p$ in $t \propto N_{\mathrm{cores}}^{-p}$")
    fig.subplots_adjust(left=0.09, right=0.98, bottom=0.27, top=0.88, wspace=0.12)
    fig.savefig(output, bbox_inches="tight"); plt.close(fig)


def main() -> None:
    rows = load()
    component_plot(rows, HERE / "Figure-7-components-ideal.pdf")
    share_plot(rows, HERE / "Figure-7-component-shares.pdf")
    exponent_plot(rows, HERE / "Figure-7-component-exponents.pdf")
    print("Wrote corrected component figures")


if __name__ == "__main__":
    main()
