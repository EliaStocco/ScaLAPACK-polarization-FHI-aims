#!/usr/bin/env python3
"""Create a Figure-7-style scalability plot from corrected timings."""

from __future__ import annotations

import csv
import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np


HERE = Path(__file__).resolve().parent
DATA = HERE / "timing_data.csv"
SUMMARY = HERE / "scaling_summary.csv"
OUTPUT = HERE / "Figure-7-corrected-scalability.pdf"
COLORS = {"LDA": "#0072B2", "HSE06": "#E69F00"}
IDEAL = "#718096"


def read_data() -> list[dict[str, object]]:
    with DATA.open(newline="") as handle:
        return [
            {**row, "cores": int(row["cores"]), "polarization_seconds": float(row["polarization_seconds"])}
            for row in csv.DictReader(handle)
        ]


def read_summary() -> dict[tuple[str, str], dict[str, float]]:
    with SUMMARY.open(newline="") as handle:
        return {
            (row["supercell"], row["functional"]): {"p": float(row["p"]), "C": float(row["prefactor_seconds"])}
            for row in csv.DictReader(handle)
        }


def add_ideal_lines(axis: plt.Axes) -> None:
    xmin, xmax = axis.get_xlim()
    ymin, ymax = axis.get_ylim()
    constants = np.logspace(np.log10(xmin * ymin), np.log10(xmax * ymax), 8)
    x = np.array([xmin, xmax])
    for constant in constants:
        axis.plot(x, constant / x, color=IDEAL, alpha=0.35, linewidth=0.5, linestyle="--", zorder=0)


def main() -> None:
    data = read_data()
    fits = read_summary()
    series = [("4x4x4", "LDA"), ("4x4x4", "HSE06"), ("8x8x8", "LDA"), ("8x8x8", "HSE06")]
    fig, axes = plt.subplots(2, 2, figsize=(8.0, 5.8), sharex=True, sharey=True)

    for axis, (supercell, functional) in zip(axes.ravel(), series):
        rows = [row for row in data if row["supercell"] == supercell and row["functional"] == functional]
        rows.sort(key=lambda row: row["cores"])
        x = np.array([row["cores"] for row in rows])
        y = np.array([row["polarization_seconds"] for row in rows])
        color = COLORS[functional]
        axis.scatter(x, y, color=color, edgecolor="black", linewidth=0.4, s=28, label="corrected polarization")
        fit = fits[(supercell, functional)]
        fit_x = np.geomspace(x.min(), x.max(), 200)
        axis.plot(fit_x, fit["C"] * fit_x ** (-fit["p"]), color=color, linestyle="--", linewidth=1.0, label=fr"fit: $p={fit['p']:.2f}$")
        axis.set_xscale("log", base=2)
        axis.set_yscale("log")
        axis.set_xlim(110, 2300)
        axis.set_ylim(y.min() * 0.65, y.max() * 1.5)
        axis.set_xticks((128, 256, 512, 1024, 2048))
        axis.get_xaxis().set_major_formatter(plt.ScalarFormatter())
        add_ideal_lines(axis)
        axis.text(0.04, 0.94, f"{supercell}, {functional}", transform=axis.transAxes, va="top", bbox={"facecolor": "white", "edgecolor": "black", "pad": 3})
        axis.grid(axis="y", color="0.82", linewidth=0.5)

    axes[0, 0].set_ylabel("Polarization overhead (s)")
    axes[1, 0].set_ylabel("Polarization overhead (s)")
    axes[1, 0].set_xlabel("n. cores")
    axes[1, 1].set_xlabel("n. cores")
    handles = [plt.Line2D([], [], marker="o", color=color, markeredgecolor="black", linestyle="", label=functional) for functional, color in COLORS.items()]
    fig.legend(handles=handles, loc="upper left", bbox_to_anchor=(0.79, 0.97), frameon=True)
    fig.subplots_adjust(left=0.10, right=0.77, bottom=0.10, top=0.96, wspace=0.16, hspace=0.16)
    fig.savefig(OUTPUT, bbox_inches="tight")
    print(f"Wrote {OUTPUT}")


if __name__ == "__main__":
    main()
