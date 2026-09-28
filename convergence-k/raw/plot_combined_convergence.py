#!/usr/bin/env python3
"""Overlay polarization and Born-charge k-grid convergence on two y-axes."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np


def load_column(path: Path, value_column: str) -> dict[int, float]:
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        required = {"k_grid", value_column}
        if reader.fieldnames is None or not required.issubset(reader.fieldnames):
            raise ValueError(f"{path} must contain: {', '.join(sorted(required))}")
        result = {int(row["k_grid"]): float(row[value_column]) for row in reader}
    if not result:
        raise ValueError(f"No data rows found in {path}")
    return result


def load_columns(path: Path, value_columns: tuple[str, ...]) -> dict[int, dict[str, float]]:
    """Read several numeric data columns indexed by ``k_grid``."""
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        required = {"k_grid", *value_columns}
        if reader.fieldnames is None or not required.issubset(reader.fieldnames):
            raise ValueError(f"{path} must contain: {', '.join(sorted(required))}")
        result = {
            int(row["k_grid"]): {column: float(row[column]) for column in value_columns}
            for row in reader
        }
    if not result:
        raise ValueError(f"No data rows found in {path}")
    return result


def main() -> None:
    base = Path(__file__).resolve().parent
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--polarization", type=Path, default=base / "polarization_delta_convergence.csv",
        help="CSV created by plot_polarization_convergence.py",
    )
    parser.add_argument(
        "--bec", type=Path,
        default=base / "bec_kgrid_convergence" / "bec-convergence" / "bec_convergence.csv",
        help="CSV created by bec_kgrid_convergence/analyse_bec_convergence.py",
    )
    parser.add_argument(
        "-o", "--output", type=Path, default=base / "polarization_bec_convergence.png",
        help="output figure (default: %(default)s)",
    )
    parser.add_argument("--show", action="store_true", help="display the figure after saving it")
    args = parser.parse_args()

    polarization = load_column(args.polarization, "delta_polarization_mC_per_m2")
    bec_columns = (
        "mean_abs_on_diagonal_difference_e",
        "std_abs_on_diagonal_difference_e",
        "mean_abs_off_diagonal_difference_e",
        "std_abs_off_diagonal_difference_e",
    )
    bec = load_columns(args.bec, bec_columns)
    grids = sorted(set(polarization) & set(bec))
    if not grids:
        raise SystemExit("The two convergence tables have no k-grid values in common.")

    figure, polarization_axis = plt.subplots(figsize=(7.0, 4.2), constrained_layout=True)
    polarization_axis.set_xscale("log")
    bec_axis = polarization_axis.twinx()
    polarization_line = polarization_axis.plot(
        grids, [polarization[grid] for grid in grids], "o-", color="tab:blue",
        linewidth=1.6, markersize=5, label=r"$\Delta P_{[111]}$",
    )
    on_diagonal = 1000*np.asarray([bec[grid]["mean_abs_on_diagonal_difference_e"] for grid in grids])
    on_diagonal_std = 1000*np.asarray([bec[grid]["std_abs_on_diagonal_difference_e"] for grid in grids])
    off_diagonal = 1000*np.asarray([bec[grid]["mean_abs_off_diagonal_difference_e"] for grid in grids])
    off_diagonal_std = 1000*np.asarray([bec[grid]["std_abs_off_diagonal_difference_e"] for grid in grids])
    on_diagonal_line = bec_axis.plot(
        grids, on_diagonal, "s-", color="tab:red", linewidth=1.6, markersize=5,
        label=r"mean $|\Delta Z^*_{\mathrm{diag}}|$",
    )
    bec_axis.fill_between(
        grids, on_diagonal - on_diagonal_std, on_diagonal + on_diagonal_std,
        color="tab:red", alpha=0.2,
    )
    off_diagonal_line = bec_axis.plot(
        grids, off_diagonal, "^-", color="tab:orange", linewidth=1.6, markersize=5,
        label=r"mean $|\Delta Z^*_{\mathrm{off-diag}}|$",
    )
    bec_axis.fill_between(
        grids, off_diagonal - off_diagonal_std, off_diagonal + off_diagonal_std,
        color="tab:orange", alpha=0.2,
    )
    polarization_axis.set(
        xlabel="Polarization k-grid length, n",
        ylabel=r"$\Delta P_{[111]}$ (mC/m$^2$)",
        title="Polarization and Born-charge convergence",
    )
    bec_axis.set_ylabel(r"mean $|\Delta Z^*|$ ($me$)")
    polarization_axis.tick_params(axis="y", labelcolor="tab:blue")
    bec_axis.tick_params(axis="y")
    polarization_axis.set_xticks(grids)
    polarization_axis.grid(True, alpha=0.3)
    lines = polarization_line + on_diagonal_line + off_diagonal_line
    polarization_axis.legend(lines, [
        line.get_label() for line in lines
    ], frameon=False)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(args.output, dpi=300)
    print(f"Saved plot: {args.output}")
    if args.show:
        plt.show()


if __name__ == "__main__":
    main()
