#!/usr/bin/env python3
"""Plot the [111] polarization error for the direct k-grid scan.

The largest available polarization string length is used as the reference.
``update_polarization_kgrid_csv.py`` must be run first to create the input CSV.
Besides the figure, this script writes a compact CSV that is also consumed by
``plot_combined_convergence.py``.
"""

from __future__ import annotations

import argparse
import csv
import math
from pathlib import Path

import matplotlib.pyplot as plt


REQUIRED_COLUMNS = {
    "polarization_kgrid_n",
    "Px_C_per_m2",
    "Py_C_per_m2",
    "Pz_C_per_m2",
}


def load_polarizations(path: Path) -> list[dict[str, float | int]]:
    """Return the [111] polarization for every completed string length."""
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None or not REQUIRED_COLUMNS.issubset(reader.fieldnames):
            raise ValueError(
                f"{path} must contain: {', '.join(sorted(REQUIRED_COLUMNS))}"
            )
        rows = [
            {
                "k_grid": int(row["polarization_kgrid_n"]),
                "polarization_111_C_per_m2": (
                    float(row["Px_C_per_m2"])
                    + float(row["Py_C_per_m2"])
                    + float(row["Pz_C_per_m2"])
                )
                / math.sqrt(3.0),
            }
            for row in reader
        ]
    if not rows:
        raise ValueError(f"No data rows found in {path}")
    return sorted(rows, key=lambda row: int(row["k_grid"]))


def write_table(rows: list[dict[str, float | int]], output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "-i", "--input", type=Path, default=Path("polarization_kgrid_convergence.csv"),
        help="input CSV created by update_polarization_kgrid_csv.py (default: %(default)s)",
    )
    parser.add_argument(
        "--table", type=Path, default=Path("polarization_delta_convergence.csv"),
        help="derived convergence table (default: %(default)s)",
    )
    parser.add_argument(
        "-o", "--output", type=Path, default=Path("polarization_delta_convergence.png"),
        help="output figure (default: %(default)s)",
    )
    parser.add_argument("--show", action="store_true", help="display the figure after saving it")
    args = parser.parse_args()

    rows = load_polarizations(args.input)
    reference = float(rows[-1]["polarization_111_C_per_m2"])
    reference_grid = int(rows[-1]["k_grid"])
    for row in rows:
        difference = abs(float(row["polarization_111_C_per_m2"]) - reference)
        row["delta_polarization_C_per_m2"] = difference
        row["delta_polarization_mC_per_m2"] = 1000.0 * difference

    write_table(rows, args.table)
    grids = [int(row["k_grid"]) for row in rows]
    differences = [float(row["delta_polarization_mC_per_m2"]) for row in rows]
    figure, axis = plt.subplots(figsize=(6.4, 4.2), constrained_layout=True)
    axis.plot(grids, differences, "o-", color="tab:blue", linewidth=1.6, markersize=5)
    axis.set(
        xlabel="Polarization k-grid length, n",
        ylabel=r"$|P_{[111]}(n) - P_{[111]}(n_{\mathrm{max}})|$ (mC/m$^2$)",
        title=rf"Polarization convergence (reference: $n = {reference_grid}$)",
    )
    axis.set_xticks(grids)
    axis.grid(True, alpha=0.3)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(args.output, dpi=300)
    print(f"Reference P_[111]: {reference:.10e} C/m^2 at n={reference_grid}")
    print(f"Wrote table: {args.table}")
    print(f"Saved plot: {args.output}")
    if args.show:
        plt.show()


if __name__ == "__main__":
    main()
