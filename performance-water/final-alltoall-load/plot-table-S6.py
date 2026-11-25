#!/usr/bin/env python3
"""Plot the scaling exponents and uncertainties reported in Table S6.

The values are copied from ``table-S6.tex``.  Parenthesized digits in the
table are interpreted as one-standard-error uncertainties, e.g. ``0.46(7)``
is plotted as ``0.46 +/- 0.07``.  The positive exponent convention is
``polarization_time = A * ncores**(-m)``.

Run from the manuscript root or from this directory, for example::

    python tables/plot-table-S6.py

The default output is ``table-S6-scaling-exponents.pdf`` in this directory. Pass a
different path with ``--output`` when another format or location is wanted.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
STYLE_FILE = ROOT / "style.mplstyle"
DEFAULT_OUTPUT = HERE / "table-S6-scaling-exponents.pdf"
sys.path.insert(0, str(ROOT / "scaling-atoms"))
from plotting_helpers import add_external_legend
# The plot is included at 0.48\linewidth in a full-width REVTeX figure.
# Generate it slightly wider than that final physical width so the included
# font is modestly smaller than 10 pt while remaining close to the main text.
LATEX_TEXT_WIDTH_IN = 7.0
INCLUDE_WIDTH_FRACTION = 0.48
FIGURE_SIZE_IN = (
    LATEX_TEXT_WIDTH_IN * INCLUDE_WIDTH_FRACTION * 1.10,
    2.28,
)

MOLECULES = (128, 196, 256)
FUNCTIONALS = ("revPBE", "HSE06", "revPBE0")
COLORS = {
    "revPBE": "#1f77b4",
    "HSE06": "#ff7f0e",
    "revPBE0": "#2ca02c",
}

# (scaling exponent m, one-standard-error uncertainty)
VALUES = {
    "revPBE": {
        128: (0.46, 0.07),
        196: (0.60, 0.04),
        256: (0.66, 0.05),
    },
    "HSE06": {
        128: (0.50, 0.05),
        196: (0.67, 0.08),
        256: (0.69, 0.14),
    },
    "revPBE0": {
        128: (0.45, 0.04),
        196: (0.60, 0.18),
        256: (0.56, 0.06),
    },
}


def plot(output: Path) -> None:
    """Create the grouped exponent bar plot and save it to ``output``."""

    output.parent.mkdir(parents=True, exist_ok=True)
    if STYLE_FILE.exists():
        plt.style.use(STYLE_FILE)

    x = np.arange(len(MOLECULES), dtype=float)
    width = 0.24
    fig, ax = plt.subplots(figsize=FIGURE_SIZE_IN)

    for index, functional in enumerate(FUNCTIONALS):
        values = np.array([VALUES[functional][n][0] for n in MOLECULES])
        errors = np.array([VALUES[functional][n][1] for n in MOLECULES])
        offset = (index - (len(FUNCTIONALS) - 1) / 2) * width
        ax.bar(
            x + offset,
            values,
            width,
            yerr=errors,
            capsize=4,
            color=COLORS[functional],
            edgecolor="black",
            linewidth=0.5,
            label=functional,
            error_kw={"elinewidth": 1.0, "capthick": 1.0},
        )

    ax.axhline(0.0, color="black", linewidth=0.8)
    ax.set_xticks(x, [str(n) for n in MOLECULES])
    ax.set_xlabel("n. molecules")
    ax.set_ylabel(r"Scaling exponent $m$")
    ax.set_ylim(0.0, 1.0)
    ax.grid(axis="y", linestyle="--", linewidth=0.5, alpha=0.35)
    add_external_legend(ax)
    fig.subplots_adjust(left=0.18, right=0.70, bottom=0.19, top=0.96)
    fig.savefig(output)
    plt.close(fig)
    print(f"Wrote {output}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        help=f"output PDF (default: {DEFAULT_OUTPUT})",
    )
    args = parser.parse_args()
    plot(args.output)


if __name__ == "__main__":
    main()
