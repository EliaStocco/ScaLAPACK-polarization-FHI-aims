#!/usr/bin/env python3

"""Combined two-panel scaling plot."""

import json
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import matplotlib.image as mpimg

from matplotlib.offsetbox import OffsetImage, AnnotationBbox

from plot import BASE, COLORS, DATA_FILE, METHOD_LABELS, STYLE_FILE


def add_lines(ax, n_lines, m, **plot_kwargs):
    """Add n_lines power-law curves with y = c*x**m scaling."""

    xmin, xmax = sorted(ax.get_xlim())
    ymin, ymax = sorted(ax.get_ylim())

    constants = np.logspace(
        np.log10(ymin / xmax**m),
        np.log10(ymax / xmin**m),
        n_lines,
    )

    # More than 2 points gives smooth curves on linear axes
    x = np.logspace(np.log10(xmin), np.log10(xmax), 200)

    for c in constants:
        ax.plot(x, c * x**m, **plot_kwargs)

    ax.set_xlim(xmin, xmax)
    ax.set_ylim(ymin, ymax)
    
# ============================================================
# Files
# ============================================================

FIT_FILE = BASE / "power-law-fits.json"
OUTPUT_FILE = BASE / "combined-scaling.pdf"


# ============================================================
# Style
# ============================================================

if STYLE_FILE.exists():
    plt.style.use(STYLE_FILE)


# ============================================================
# Shared helpers
# ============================================================

def power_law(x, A, m):
    """Evaluate y = A x^m."""
    return A * x**m


def clean_data(df, quantity):
    """Return valid positive x and y data."""

    subset = df[["atoms", quantity]].dropna()

    subset = subset[
        (subset["atoms"] > 0)
        & (subset[quantity] > 0)
    ].sort_values("atoms")

    return (
        subset["atoms"].to_numpy(dtype=float),
        subset[quantity].to_numpy(dtype=float),
    )


def add_linear_scaling_lines(ax, n_lines, **plot_kwargs):
    """Add guide lines with y = c*x."""

    xmin, xmax = sorted(ax.get_xlim())
    ymin, ymax = sorted(ax.get_ylim())

    constants = np.logspace(
        np.log10(ymin / xmax),
        np.log10(ymax / xmin),
        n_lines,
    )

    x = np.logspace(
        np.log10(xmin),
        np.log10(xmax),
        2,
    )

    for c in constants:
        ax.plot(x, c * x, **plot_kwargs)

    ax.set_xlim(xmin, xmax)
    ax.set_ylim(ymin, ymax)


def add_cubic_scaling_lines(ax, n_lines, **plot_kwargs):
    """Add guide lines with y = c*x**3."""

    xmin, xmax = sorted(ax.get_xlim())
    ymin, ymax = sorted(ax.get_ylim())

    constants = np.logspace(
        np.log10(ymin / xmax**3),
        np.log10(ymax / xmin**3),
        n_lines,
    )

    x = np.logspace(
        np.log10(xmin),
        np.log10(xmax),
        200,
    )

    for c in constants:
        ax.plot(x, c * x**3, **plot_kwargs)

    ax.set_xlim(xmin, xmax)
    ax.set_ylim(ymin, ymax)


# ============================================================
# Right-panel definitions
# ============================================================

SCALAPACK_QUANTITIES = [
    "wannier_time",
    "fourier_ev_time",
    "dipole_matrix_time",
    "dipole_term_time",
    "berry_term_time",
]

LABELS = {
    "polarization_time": "Polarization",
    "wannier_time": "Polarization (total)",
    "fourier_ev_time": "Fourier interpolation",
    "dipole_matrix_time": "Dipole matrix",
    "dipole_term_time": "Dipole term",
    "berry_term_time": "Berry term",
    "converge_time": "Density convergence",
}


# ============================================================
# Left subplot
# ============================================================

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

        ax.plot(
            xfit,
            yfit,
            color=COLORS[method],
            linestyle="--",
            linewidth=1.0,
            alpha=0.7,
        )

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

        ax.text(
            0.30,
            0.33,
            f"$m={m}$",
            transform=ax.transAxes,
            rotation=40,
            ha="center",
            va="center",
            color=COLORS["lapack"],
        )

    if "scalapack" in fit:

        m = np.round(
            fit["scalapack"],
            1,
        )

        ax.text(
            0.60,
            0.40,
            f"$m={m}$",
            transform=ax.transAxes,
            rotation=33,
            ha="center",
            va="center",
            color=COLORS["scalapack"],
        )

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


# ============================================================
# Right subplot
# ============================================================

def plot_right_panel(ax, df, fits):
    """Plot individual timing contributions."""

    df = df[df["nodes"] == 2].copy()
    df = df[df["atoms"] != 686]

    scalapack = df[
        df["method"] == "scalapack"
    ].copy()

    # --------------------------------------------------------
    # Charge-density convergence
    # --------------------------------------------------------
    if (
        "converge_time" in df.columns
        and "converge_time" in fits
    ):

        quantity = "converge_time"

        converge = (
            df[["atoms", quantity]]
            .dropna()
            .drop_duplicates(subset=["atoms"])
            .sort_values("atoms")
        )

        x, y = clean_data(
            converge,
            quantity,
        )

        if len(x) > 0:

            # Main line + marker.
            #
            # This object is used for the legend.
            # alpha=0.8 applies to both here.
            line = ax.plot(
                x,
                y,
                marker="o",
                linestyle="-",
                alpha=0.8,
                label=LABELS.get(
                    quantity,
                    quantity,
                ),
            )[0]

            # Overlay fully opaque markers.
            #
            # These do NOT create another legend entry.
            ax.plot(
                x,
                y,
                linestyle="none",
                marker="o",
                color=line.get_color(),
                alpha=1.0,
                label="_nolegend_",
            )

    # --------------------------------------------------------
    # ScaLAPACK quantities
    # --------------------------------------------------------
    for quantity in SCALAPACK_QUANTITIES:

        if quantity not in scalapack.columns:
            continue

        if quantity not in fits:
            continue

        x, y = clean_data(
            scalapack,
            quantity,
        )

        if len(x) == 0:
            continue

        linestyle = (
            "-"
            if quantity == "wannier_time"
            else "--"
        )

        # Main line + marker.
        #
        # This object provides the legend handle.
        line = ax.plot(
            x,
            y,
            marker="o",
            linestyle=linestyle,
            alpha=0.8,
            label=LABELS.get(
                quantity,
                quantity,
            ),
        )[0]

        # Overlay opaque markers.
        ax.plot(
            x,
            y,
            linestyle="none",
            marker="o",
            color=line.get_color(),
            alpha=1.0,
            label="_nolegend_",
        )

    # --------------------------------------------------------
    # Axes
    # --------------------------------------------------------
    ax.set_xscale(
        "log",
        base=2,
    )

    ax.set_yscale(
        "log",
        base=10,
    )

    ax.set_xlabel("n. atoms")
    ax.set_ylabel("CPU time (s)")

    # --------------------------------------------------------
    # X ticks
    # --------------------------------------------------------
    xticks = sorted(
        df["atoms"].unique()
    )

    ax.xaxis.set_major_locator(
        mticker.FixedLocator(
            xticks
        )
    )

    ax.xaxis.set_major_formatter(
        mticker.FormatStrFormatter(
            "%d"
        )
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
        label.set_horizontalalignment(
            "right"
        )

    # --------------------------------------------------------
    # Legend
    # --------------------------------------------------------
    ax.legend(
        ncol=1,
    )

    # --------------------------------------------------------
    # Ideal cubic scaling guides
    # --------------------------------------------------------
    # add_cubic_scaling_lines(
    #     ax,
    #     n_lines=20,
    #     color="gray",
    #     alpha=0.5,
    #     linewidth=0.5,
    #     linestyle="--",
    # )
    
    xmin, xmax = sorted(ax.get_xlim())
    ymin, ymax = sorted(ax.get_ylim())
    # constants = [0.3,0.4,0.5]

    # More than 2 points gives smooth curves on linear axes
    x = np.logspace(np.log10(xmin), np.log10(xmax), 2)
    ax.plot(x, 0.3 * x, color="gray", alpha=0.5,linestyle="-" )
    for c in [1e-4]:
        ax.plot(x, c * x**2, color="gray", alpha=0.5,linestyle="-" )
    # ax.plot(x, 1e- * x**2, color="gray", alpha=0.5,linestyle="-" )
    
    ax.text(
        20, 7,
        r"linear scaling",
        # transform=ax.transAxes,
        rotation=9,      # angle in degrees
        ha="left",
        va="bottom",
        color="gray"
    )
    
    ax.text(
        400, 7,
        r"quadratic scaling",
        # transform=ax.transAxes,
        rotation=20,      # angle in degrees
        ha="left",
        va="bottom",
        color="gray"
    )
    
    ax.text(
        15, 400,
        r"ScaLAPACK",
        ha="left",
        va="bottom",
        bbox=dict(
            facecolor="white",
            edgecolor="black",
            boxstyle="round,pad=0.4",  # more space
            alpha=1,
        ),
    )

    ax.set_xlim(xmin, xmax)
    ax.set_ylim(ymin, ymax)


# ============================================================
# Main
# ============================================================

def main():

    # --------------------------------------------------------
    # Load data
    # --------------------------------------------------------
    df = pd.read_csv(
        DATA_FILE
    )

    if df.empty:
        raise RuntimeError(
            f"No data found in {DATA_FILE}"
        )

    # --------------------------------------------------------
    # Load fitted parameters
    # --------------------------------------------------------
    with FIT_FILE.open() as f:
        fits = json.load(f)

    # --------------------------------------------------------
    # Figure
    #
    # Left : Right width = 1 : 2
    # --------------------------------------------------------
    fig, (ax_left, ax_right) = plt.subplots(
        1,
        2,
        figsize=(9, 3.5),
        gridspec_kw={
            "width_ratios": [1, 2],
        },
    )

    # --------------------------------------------------------
    # Individual panels
    # --------------------------------------------------------
    plot_left_panel(
        ax_left,
        df,
    )

    plot_right_panel(
        ax_right,
        df,
        fits,
    )

    # --------------------------------------------------------
    # Layout and output
    # --------------------------------------------------------
    fig.tight_layout()

    fig.savefig(
        OUTPUT_FILE,
        bbox_inches="tight",
    )

    print(
        f"Saved {OUTPUT_FILE}"
    )


if __name__ == "__main__":
    main()