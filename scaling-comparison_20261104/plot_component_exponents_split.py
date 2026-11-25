#!/usr/bin/env python3
"""Create separate scalability-exponent and resolved cost-share figures."""

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

import plot_component_exponents as base


def load_series():
    data = pd.read_csv(base.DATA_FILE)
    dense = pd.read_csv(base.DENSE_DATA_FILE)
    return {
        **{
            sid: data[data["series_id"] == sid].sort_values("cores")
            for sid in base.SERIES
        },
        **{
            sid: dense[dense["series_id"] == sid].sort_values("cores")
            for sid in base.DENSE_SERIES
        },
    }


LABELS = [
    "4×4×4\nLDA", "4×4×4\nHSE06", "4×4×4\nLDA\n(dense)",
    "8×8×8\nLDA", "8×8×8\nHSE06", "8×8×8\nLDA\n(dense)",
]
SHARE_TITLES = [label.replace("\n(dense)", " (dense)").replace("\n", ", ") for label in LABELS]


def plot_exponents(series, output: Path) -> None:
    fig, ax = plt.subplots(figsize=(9.0, 3.5))
    x = np.arange(len(base.PLOT_SERIES), dtype=float)
    width = 0.15
    handles = []
    for index, (column, label, color) in enumerate(base.COMPONENTS):
        values, errors = [], []
        for sid in base.PLOT_SERIES:
            frame = series[sid]
            fit = base.fit_loglog(frame["cores"].to_numpy(float), frame[column].to_numpy(float))
            values.append(np.nan if fit is None else fit[0])
            errors.append(0.0 if fit is None else fit[1])
        bars = ax.bar(
            x + (index - 2) * width, values, width, yerr=errors,
            capsize=3, color=color, edgecolor="black", linewidth=0.45,
            label=label, error_kw={"elinewidth": 0.8, "capthick": 0.8},
        )
        handles.append(bars)
    ax.set_xticks(x, LABELS, rotation=30, ha="center")
    ax.set_ylabel(r"Scalability exponent $m$")
    ax.set_ylim(0, 1.45)
    ax.grid(axis="y", linestyle="--", linewidth=0.5, alpha=0.35)
    legend = ax.legend(
        handles,
        [label for _, label, _ in base.COMPONENTS],
        loc="upper left",
        bbox_to_anchor=(1.01, 1),
        borderaxespad=0,
        frameon=True,
        facecolor="white",
        edgecolor="black",
        framealpha=1.0,
    )
    fig.subplots_adjust(left=0.10, right=0.70, bottom=0.25, top=0.96)
    fig.savefig(output)
    plt.close(fig)


def plot_shares(series, output: Path) -> None:
    fig, axes = plt.subplots(2, 3, figsize=(10.5, 5.0), sharey=True)
    axes = axes.ravel()
    handles = []
    for index, (sid, ax) in enumerate(zip(base.PLOT_SERIES, axes)):
        frame = series[sid]
        cores = frame["cores"].to_numpy(float)
        values = frame[[column for column, _, _ in base.SHARE_COMPONENTS]].to_numpy(float)
        values[~np.isfinite(values)] = 0
        values = np.maximum(values, 0)
        totals = values.sum(axis=1)
        shares = np.divide(100 * values, totals[:, None], out=np.zeros_like(values), where=totals[:, None] != 0)
        positions = np.arange(len(cores), dtype=float)
        bottom = np.zeros(len(cores))
        for component_index, (_, label, color) in enumerate(base.SHARE_COMPONENTS):
            bars = ax.bar(positions, shares[:, component_index], 1.0, bottom=bottom, color=color, edgecolor="black", linewidth=0.4, label=label)
            if index == 0:
                handles.append(bars)
            bottom += shares[:, component_index]
        ax.set_title(SHARE_TITLES[index])
        ax.set_xlim(-0.5, len(cores) - 0.5)
        ax.set_xticks(positions, [str(int(core)) for core in cores])
        ax.set_ylim(0, 100)
        ax.set_yticks((0, 25, 50, 75, 100))
        ax.grid(axis="y", linestyle="--", linewidth=0.5, alpha=0.35)
        if index % 3 == 0:
            ax.set_ylabel(r"Cost share (\%)")
        else:
            ax.set_yticklabels([])
        if index < 3:
            ax.set_xticklabels([])
        else:
            ax.set_xlabel("n. cores")
    fig.legend(
        handles,
        [label for _, label, _ in base.SHARE_COMPONENTS],
        loc="upper left",
        bbox_to_anchor=(0.72, 0.89),
        borderaxespad=0,
        frameon=True,
        facecolor="white",
        edgecolor="black",
        framealpha=1.0,
    )
    fig.subplots_adjust(left=0.07, right=0.70, bottom=0.13, top=0.89, wspace=0.12, hspace=0.22)
    fig.savefig(output)
    plt.close(fig)


def main() -> None:
    series = load_series()
    output_dir = base.HERE
    plot_exponents(series, output_dir / "Figure-7-component-exponents.pdf")
    plot_shares(series, output_dir / "Figure-7-component-shares.pdf")
    print(f"Wrote {output_dir / 'Figure-7-component-exponents.pdf'}")
    print(f"Wrote {output_dir / 'Figure-7-component-shares.pdf'}")


if __name__ == "__main__":
    main()
