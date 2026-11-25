#!/usr/bin/env python3
"""Plot Figure S1 component exponents and atom-resolved cost shares."""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
DATA_FILE = HERE / "dataframe.csv"
FIGURES = HERE

COMPONENTS = (
    ("polarization_time", "Polarization (total)", "#0072B2"),
    ("fourier_ev_time", "Fourier interpolation", "#E69F00"),
    ("dipole_matrix_time", "Dipole matrix", "#009E73"),
    ("dipole_term_time", "Dipole term", "#D55E00"),
    ("berry_term_time", "Berry term", "#CC79A7"),
)
SHARE_COMPONENTS = COMPONENTS[1:]


def fit_loglog(x: np.ndarray, y: np.ndarray) -> tuple[float, float] | None:
    valid = np.isfinite(x) & np.isfinite(y) & (x > 0) & (y > 0)
    if valid.sum() < 3:
        return None
    lx, ly = np.log(x[valid]), np.log(y[valid])
    slope, intercept = np.polyfit(lx, ly, 1)
    residuals = ly - (intercept + slope * lx)
    error = np.sqrt(
        np.sum(residuals**2) / (len(lx) - 2)
        / np.sum((lx - lx.mean()) ** 2)
    )
    # Keep the signed log-log slope: y = A * x**m.  Timings that decrease
    # with system size therefore have a negative exponent.
    return float(slope), float(error)


def load_data() -> pd.DataFrame:
    data = pd.read_csv(DATA_FILE)
    data = data[data["method"] == "scalapack"].sort_values("atoms").copy()
    required = {column for column, _, _ in COMPONENTS} | {"atoms"}
    missing = required - set(data.columns)
    if missing:
        raise ValueError(f"Missing columns: {sorted(missing)}")
    return data


def plot_exponents(data: pd.DataFrame, ax: plt.Axes, *, legend: bool = True) -> None:
    x = np.arange(len(COMPONENTS), dtype=float)
    values, errors = [], []
    atoms = data["atoms"].to_numpy(float)
    for column, _, _ in COMPONENTS:
        fit = fit_loglog(atoms, data[column].to_numpy(float))
        values.append(np.nan if fit is None else fit[0])
        errors.append(0.0 if fit is None else fit[1])

    bars = []
    for index, ((_, label, color), value, error) in enumerate(zip(COMPONENTS, values, errors)):
        bars.extend(ax.bar(index, value, yerr=error, color=color, edgecolor="black", linewidth=0.45, capsize=3, label=label, error_kw={"elinewidth": 0.8, "capthick": 0.8}))
    ax.set_xticks(x, ["total", "Fourier", "Dipole matrix", "Dipole term", "Berry term"])
    ax.set_ylabel(r"Scaling exponent $m$")
    finite_values = np.asarray(values)[np.isfinite(values)]
    margin = max(np.ptp(finite_values) * 0.15, 0.1)
    ax.set_ylim(finite_values.min() - margin, finite_values.max() + margin)
    ax.axhline(0, color="black", linewidth=0.7)
    ax.grid(axis="y", linestyle="--", linewidth=0.5, alpha=0.35)
    if legend:
        ax.legend(loc="upper left", bbox_to_anchor=(1.01, 1), borderaxespad=0, frameon=True, facecolor="white", edgecolor="black", framealpha=1)


def plot_shares(data: pd.DataFrame, ax: plt.Axes, *, legend: bool = True) -> None:
    atoms = data["atoms"].to_numpy(int)
    values = data[[column for column, _, _ in SHARE_COMPONENTS]].to_numpy(float)
    values[~np.isfinite(values)] = 0
    values = np.maximum(values, 0)
    totals = values.sum(axis=1)
    shares = np.divide(100 * values, totals[:, None], out=np.zeros_like(values), where=totals[:, None] != 0)

    positions = np.arange(len(atoms), dtype=float)
    bottom = np.zeros(len(atoms))
    handles = []
    for index, (_, label, color) in enumerate(SHARE_COMPONENTS):
        bars = ax.bar(positions, shares[:, index], 1.0, bottom=bottom, color=color, edgecolor="black", linewidth=0.4, label=label)
        handles.append(bars)
        bottom += shares[:, index]
    ax.set_xticks(positions, [str(atom) for atom in atoms])
    ax.set_xlabel("n. atoms")
    ax.set_ylabel(r"Cost share (\%)")
    ax.set_xlim(-0.5, len(atoms) - 0.5)
    ax.set_ylim(0, 100)
    ax.set_yticks((0, 25, 50, 75, 100))
    ax.grid(axis="y", linestyle="--", linewidth=0.5, alpha=0.35)
    if legend:
        ax.legend(handles, [label for _, label, _ in SHARE_COMPONENTS], loc="upper left", bbox_to_anchor=(1.01, 1), borderaxespad=0, frameon=True, facecolor="white", edgecolor="black", framealpha=1)


def main() -> None:
    FIGURES.mkdir(parents=True, exist_ok=True)
    data = load_data()
    fig, axes = plt.subplots(1, 2, figsize=(8.4, 3.2), gridspec_kw={"width_ratios": (1.0, 1.15)})
    plot_exponents(data, axes[0], legend=False)
    plot_shares(data, axes[1], legend=False)
    axes[0].tick_params(axis="x", which="major", labelrotation=45)
    for label in axes[0].get_xticklabels():
        label.set_horizontalalignment("center")

    handles = [plt.Rectangle((0, 0), 1, 1, color=color, edgecolor="black", linewidth=0.45)
               for _, _, color in SHARE_COMPONENTS]
    labels = [label for _, label, _ in SHARE_COMPONENTS]
    fig.subplots_adjust(left=0.10, right=0.70, bottom=0.19, top=0.89, wspace=0.28)
    fig.legend(handles, labels, loc="upper left", ncol=1, frameon=True,
               facecolor="white", edgecolor="black", framealpha=1,
               bbox_to_anchor=(0.72, 0.89), borderaxespad=0)
    output = FIGURES / "Figure-S1-components.pdf"
    fig.savefig(output, bbox_inches="tight")
    plt.close(fig)
    print(f"Wrote {output}")


if __name__ == "__main__":
    main()
