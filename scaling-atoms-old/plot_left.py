#!/usr/bin/env python3

"""Standalone left-panel scaling plot."""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import matplotlib.image as mpimg

from matplotlib.offsetbox import OffsetImage, AnnotationBbox

from plot import BASE, COLORS, DATA_FILE, METHOD_LABELS, STYLE_FILE


OUTPUT_FILE = BASE / "scaling-left.pdf"


if STYLE_FILE.exists():
    plt.style.use(STYLE_FILE)


def plot_left_panel(ax, df):
    """Plot total polarization scaling on two nodes."""

    df = df[df["nodes"] == 2].copy()
    df = df[df["atoms"] != 686]
    df = df.sort_values(["method", "atoms"])

    fit = {}

    # --------------------------------------------------------
    # Data + power-law fits
    # --------------------------------------------------------
    for method in ("lapack", "scalapack"):

        subset = df[df["method"] == method]

        if subset.empty:
            continue

        xdata = subset["atoms"].to_numpy(dtype=float)

        ydata = (
            subset["polarization_time"] / 3600.0
        ).to_numpy(dtype=float)

        # Data
        ax.plot(
            xdata,
            ydata,
            color=COLORS[method],
            marker="o",
            linewidth=1.2,
            markersize=4,
            label=METHOD_LABELS[method],
        )

        # Power-law fit: y = A x^m
        m, logA = np.polyfit(
            np.log(xdata),
            np.log(ydata),
            1,
        )

        A = np.exp(logA)
        fit[method] = m

        xfit = np.logspace(
            np.log10(xdata.min()),
            np.log10(xdata.max()),
            200,
        )

        yfit = A * xfit**m

        # ax.plot(
        #     xfit,
        #     yfit,
        #     color=COLORS[method],
        #     linestyle="--",
        #     linewidth=1.0,
        #     alpha=0.7,
        # )

        print(
            f"{method}: "
            f"y = {A:.4e} x^{m:.4f}"
        )

    # --------------------------------------------------------
    # Axes
    # --------------------------------------------------------
    ax.set_xscale("log", base=2)
    ax.set_yscale("log", base=2)

    ax.set_ylim(None, 24.0)

    ax.set_xlabel("n. atoms")
    ax.set_ylabel("CPU time")

    # --------------------------------------------------------
    # Y ticks
    # --------------------------------------------------------
    time_ticks = [
        0.1 / 3600.0,
        1.0 / 3600.0,
        1.0 / 60.0,
        1.0,
        24.0,
    ]

    time_labels = [
        "",
        "1 s",
        "1 m",
        "1 h",
        "1 day",
    ]

    ax.yaxis.set_major_locator(
        mticker.FixedLocator(time_ticks)
    )

    ax.yaxis.set_major_formatter(
        mticker.FixedFormatter(time_labels)
    )

    # --------------------------------------------------------
    # X ticks
    # --------------------------------------------------------
    xticks = sorted(df["atoms"].unique())

    ax.xaxis.set_major_locator(
        mticker.FixedLocator(xticks)
    )

    ax.xaxis.set_major_formatter(
        mticker.FormatStrFormatter("%d")
    )

    ax.tick_params(
        axis="x",
        which="minor",
        length=3,
    )

    ax.tick_params(
        axis="x",
        which="major",
        length=4,
        labelrotation=35,
    )

    for label in ax.get_xticklabels():
        label.set_horizontalalignment("right")

    # --------------------------------------------------------
    # Legend
    # --------------------------------------------------------
    legend = ax.legend(loc="upper left")

    legend.get_frame().set_facecolor("white")
    legend.get_frame().set_edgecolor("black")
    legend.get_frame().set_alpha(1.0)

    # --------------------------------------------------------
    # Supercell images
    # --------------------------------------------------------
    image_specs = [
        ("supercell.2.png", 0.015, (0.08, 0.20)),
        ("supercell.4.png", 0.030, (0.45, 0.55)),
        ("supercell.8.png", 0.050, (0.70, 0.20)),
    ]

    for filename, zoom, position in image_specs:

        img = mpimg.imread(filename)

        imagebox = OffsetImage(
            img,
            zoom=zoom,
        )

        ab = AnnotationBbox(
            imagebox,
            position,
            xycoords="axes fraction",
            frameon=False,
        )

        ax.add_artist(ab)

    # --------------------------------------------------------
    # Arrows
    # --------------------------------------------------------
    ax.annotate(
        "",
        xy=(1000, 3.0),
        xytext=(500, 0.005),
        arrowprops=dict(
            arrowstyle="->",
            connectionstyle="arc3,rad=0.1",
            linewidth=0.5,
            alpha=0.8,
        ),
    )

    ax.annotate(
        "",
        xy=(1000, 0.1),
        xytext=(600, 0.005),
        arrowprops=dict(
            arrowstyle="->",
            connectionstyle="arc3,rad=0.1",
            linewidth=0.5,
            alpha=0.8,
        ),
    )

    # --------------------------------------------------------
    # Scaling labels
    # --------------------------------------------------------
    if "lapack" in fit:

        m = np.round(
            fit["lapack"],
            1,
        )

        # ax.text(
        #     0.30,
        #     0.33,
        #     f"$m={m}$",
        #     transform=ax.transAxes,
        #     rotation=40,
        #     ha="center",
        #     va="center",
        #     color=COLORS["lapack"],
        # )

    if "scalapack" in fit:

        m = np.round(
            fit["scalapack"],
            1,
        )

        # ax.text(
        #     0.60,
        #     0.40,
        #     f"$m={m}$",
        #     transform=ax.transAxes,
        #     rotation=33,
        #     ha="center",
        #     va="center",
        #     color=COLORS["scalapack"],
        # )

    # # --------------------------------------------------------
    # # Ideal linear scaling guides
    # # --------------------------------------------------------
    # add_linear_scaling_lines(
    #     ax,
    #     n_lines=20,
    #     color="gray",
    #     alpha=0.5,
    #     linewidth=0.5,
    #     linestyle="--",
    # )

def main():
    df = pd.read_csv(DATA_FILE)

    if df.empty:
        raise RuntimeError(f"No data found in {DATA_FILE}")

    fig, ax = plt.subplots(figsize=(3, 3))
    plot_left_panel(ax, df)

    fig.tight_layout()
    fig.savefig(OUTPUT_FILE, bbox_inches="tight")

    print(f"Saved {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
