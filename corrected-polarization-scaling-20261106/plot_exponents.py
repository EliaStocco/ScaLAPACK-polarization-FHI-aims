#!/usr/bin/env python3
"""Plot corrected strong-scalability exponents."""

from __future__ import annotations

import csv
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np


HERE = Path(__file__).resolve().parent
SUMMARY = HERE / "scaling_summary.csv"
OUTPUT = HERE / "Figure-7-corrected-exponents.pdf"
COLORS = {"LDA": "#0072B2", "HSE06": "#E69F00"}


def main() -> None:
    with SUMMARY.open(newline="") as handle:
        rows = list(csv.DictReader(handle))
    labels = [f"{row['supercell']}\n{row['functional']}" for row in rows]
    values = np.array([float(row["p"]) for row in rows])
    colors = [COLORS[row["functional"]] for row in rows]
    fig, axis = plt.subplots(figsize=(6.2, 3.4))
    axis.bar(np.arange(len(rows)), values, color=colors, edgecolor="black", linewidth=0.45)
    axis.set_xticks(np.arange(len(rows)), labels)
    axis.set_ylabel(r"Scalability exponent $p$ in $t \propto N_{\mathrm{cores}}^{-p}$")
    axis.set_ylim(0, max(values) * 1.25)
    axis.axhline(1, color="#718096", linestyle="--", linewidth=0.8, label="ideal scalability")
    axis.grid(axis="y", linestyle="--", linewidth=0.5, alpha=0.35)
    axis.legend(frameon=True)
    fig.tight_layout()
    fig.savefig(OUTPUT, bbox_inches="tight")
    print(f"Wrote {OUTPUT}")


if __name__ == "__main__":
    main()
