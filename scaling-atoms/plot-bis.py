#!/usr/bin/env python3

"""Plot two-node polarization timings and relative polarization cost."""

import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import matplotlib.image as mpimg
import pandas as pd
import numpy as np
from matplotlib.offsetbox import OffsetImage, AnnotationBbox

from plot import BASE, COLORS, DATA_FILE, METHOD_LABELS, STYLE_FILE

OUTPUT_FILE = BASE / "scaling-2-nodes.pdf"


def add_lines(ax, n_lines, **plot_kwargs):
    """Add n_lines reference lines with y = c*x scaling."""

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
        ax.plot(
            x,
            c * x,
            **plot_kwargs,
        )

    ax.set_xlim(xmin, xmax)
    ax.set_ylim(ymin, ymax)


# ---------------------------------------------------------
# Load data
# ---------------------------------------------------------
df = pd.read_csv(DATA_FILE)

required = {
    "nodes",
    "supercell",
    "atoms",
    "method",
    "scf_time",
    "dipole_time",
    "polarization_time",
    "converge_time",
}

missing = required - set(df.columns)

if missing:
    raise ValueError(
        f"Missing columns in {DATA_FILE}: {sorted(missing)}"
    )

if df.empty:
    raise RuntimeError(f"No data found in {DATA_FILE}")


# ---------------------------------------------------------
# Style
# ---------------------------------------------------------
if STYLE_FILE.exists():
    plt.style.use(STYLE_FILE)


# ---------------------------------------------------------
# Select two-node calculations
# ---------------------------------------------------------
df = df[df["nodes"] == 2].copy()
df = df.sort_values(["method", "atoms"])

# Top panel: retain the original exclusion of 686 atoms
df_top = df[df["atoms"] != 686].copy()

# Bottom panel: all ScaLAPACK points with convergence data
df_ratio = df[
    (df["method"] == "scalapack")
    & df["polarization_time"].notna()
    & df["converge_time"].notna()
].copy()

df_ratio = df_ratio[
    (df_ratio["atoms"] > 0)
    & (df_ratio["polarization_time"] > 0)
    & (df_ratio["converge_time"] > 0)
]

df_ratio["relative_cost"] = (
    df_ratio["polarization_time"]
    / df_ratio["converge_time"]
)

df_ratio = df_ratio.sort_values("atoms")
df_ratio = df_ratio[ df_ratio["atoms"] != 686 ]


# ---------------------------------------------------------
# Create figure
# ---------------------------------------------------------
fig, (ax, ax_ratio) = plt.subplots(
    2,
    1,
    figsize=(3, 4),
    gridspec_kw={
        "height_ratios": [2.2, 1.0],
        "hspace": 0.12,
    },
)


# =========================================================
# TOP PANEL
# =========================================================

fit = {}

for method in ("lapack", "scalapack"):

    subset = df_top[df_top["method"] == method]

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

    fit[method] = {
        "A": A,
        "m": m,
    }

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


# ---------------------------------------------------------
# Top axes
# ---------------------------------------------------------
ax.set_xscale("log", base=2)
ax.set_yscale("log", base=2)

ax.set_ylim(None, 24.0)

ax.set_ylabel("CPU time")

ax.tick_params(
    axis="x",
    labelbottom=False,
)


# ---------------------------------------------------------
# Top Y ticks
# ---------------------------------------------------------
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


# ---------------------------------------------------------
# Top X ticks
# ---------------------------------------------------------
xticks_top = sorted(df_top["atoms"].unique())

ax.xaxis.set_major_locator(
    mticker.FixedLocator(xticks_top)
)

ax.xaxis.set_major_formatter(
    mticker.FormatStrFormatter("%d")
)


# ---------------------------------------------------------
# Legend
# ---------------------------------------------------------
legend = ax.legend(loc="upper left")

legend.get_frame().set_facecolor("white")
legend.get_frame().set_edgecolor("black")
legend.get_frame().set_alpha(1.0)


# ---------------------------------------------------------
# Images
# ---------------------------------------------------------
img = mpimg.imread("supercell.2.png")
imagebox = OffsetImage(img, zoom=0.015)

ab = AnnotationBbox(
    imagebox,
    (0.08, 0.2),
    xycoords="axes fraction",
    frameon=False,
)

ax.add_artist(ab)


img = mpimg.imread("supercell.4.png")
imagebox = OffsetImage(img, zoom=0.03)

ab = AnnotationBbox(
    imagebox,
    (0.45, 0.55),
    xycoords="axes fraction",
    frameon=False,
)

ax.add_artist(ab)


img = mpimg.imread("supercell.8.png")
imagebox = OffsetImage(img, zoom=0.05)

ab = AnnotationBbox(
    imagebox,
    (0.7, 0.2),
    xycoords="axes fraction",
    frameon=False,
)

ax.add_artist(ab)


# ---------------------------------------------------------
# Arrows
# ---------------------------------------------------------
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


# ---------------------------------------------------------
# Top ideal-scaling guides
# ---------------------------------------------------------
add_lines(
    ax,
    n_lines=20,
    color="gray",
    alpha=0.5,
    linewidth=0.5,
    linestyle="--",
)


# ---------------------------------------------------------
# Top annotations
# ---------------------------------------------------------
ax.text(
    0.3,
    0.7,
    r"ideal scaling: $m=1$",
    transform=ax.transAxes,
    rotation=16,
    ha="center",
    va="center",
    color="gray",
)


ax.text(
    0.3,
    0.34,
    rf"$m={fit['lapack']['m']:.1f}$",
    transform=ax.transAxes,
    rotation=40,
    ha="center",
    va="center",
    color=COLORS["lapack"],
)


ax.text(
    0.6,
    0.41,
    rf"$m={fit['scalapack']['m']:.1f}$",
    transform=ax.transAxes,
    rotation=33,
    ha="center",
    va="center",
    color=COLORS["scalapack"],
)


# =========================================================
# BOTTOM PANEL
# =========================================================

xdata = df_ratio["atoms"].to_numpy(dtype=float)
ydata = df_ratio["relative_cost"].to_numpy(dtype=float)


# ---------------------------------------------------------
# Data
# ---------------------------------------------------------
ax_ratio.plot(
    xdata,
    ydata,
    color=COLORS["scalapack"],
    marker="o",
    linewidth=1.2,
    markersize=4,
)


# ---------------------------------------------------------
# Power-law fit: y = A x^m
# ---------------------------------------------------------
m_ratio, logA_ratio = np.polyfit(
    np.log(xdata),
    np.log(ydata),
    1,
)

A_ratio = np.exp(logA_ratio)

xfit = np.logspace(
    np.log10(xdata.min()),
    np.log10(xdata.max()),
    200,
)

yfit = A_ratio * xfit**m_ratio

ax_ratio.plot(
    xfit,
    yfit,
    color=COLORS["scalapack"],
    linestyle="--",
    linewidth=1.0,
    alpha=0.7,
)

print(
    f"relative_cost: "
    f"y = {A_ratio:.4e} x^{m_ratio:.4f}"
)


# ---------------------------------------------------------
# Bottom axes
# ---------------------------------------------------------
ax_ratio.set_xscale("log", base=2)
ax_ratio.set_yscale("log", base=10)

ax_ratio.set_xlabel("n. atoms")

ax_ratio.set_ylabel(
    r"$t_{\mathrm{pol}}/t_{\mathrm{SCF}}$"
)


# ---------------------------------------------------------
# Bottom Y ticks:
#
# display 0.1 and 1 instead of 10^-1 and 10^0
# ---------------------------------------------------------
ax_ratio.yaxis.set_major_locator(
    mticker.FixedLocator([
        0.1,
        1.0,
    ])
)

ax_ratio.yaxis.set_major_formatter(
    mticker.FixedFormatter([
        "0.1",
        "1",
    ])
)

ax_ratio.yaxis.set_minor_locator(
    mticker.LogLocator(
        base=10,
        subs=np.arange(2, 10) * 0.1,
    )
)

ax_ratio.yaxis.set_minor_formatter(
    mticker.NullFormatter()
)


# ---------------------------------------------------------
# Bottom X ticks
# ---------------------------------------------------------
xticks_ratio = sorted(df_ratio["atoms"].unique())

ax_ratio.xaxis.set_major_locator(
    mticker.FixedLocator(xticks_ratio)
)

ax_ratio.xaxis.set_major_formatter(
    mticker.FormatStrFormatter("%d")
)

ax_ratio.xaxis.set_minor_locator(
    mticker.NullLocator()
)

ax_ratio.tick_params(
    axis="x",
    which="major",
    length=4,
    labelrotation=35,
)

for label in ax_ratio.get_xticklabels():
    label.set_horizontalalignment("right")


# ---------------------------------------------------------
# Bottom ideal-scaling guides
# ---------------------------------------------------------
add_lines(
    ax_ratio,
    n_lines=12,
    color="gray",
    alpha=0.5,
    linewidth=0.5,
    linestyle="--",
)


# ---------------------------------------------------------
# Bottom fit annotation
# ---------------------------------------------------------
ax_ratio.text(
    0.55,
    0.62,
    rf"$m={m_ratio:.1f}$",
    transform=ax_ratio.transAxes,
    rotation=25,
    ha="center",
    va="center",
    color=COLORS["scalapack"],
)


# ---------------------------------------------------------
# Print ratio values
# ---------------------------------------------------------
print()
print("atoms   t_pol / t_SCF")
print("---------------------")

for _, row in df_ratio.iterrows():
    print(
        f"{int(row['atoms']):5d}   "
        f"{row['relative_cost']:.6f}"
    )


# ---------------------------------------------------------
# Layout and output
# ---------------------------------------------------------
fig.subplots_adjust(
    left=0.20,
    right=0.98,
    bottom=0.15,
    top=0.98,
    hspace=0.12,
)

plt.savefig(
    OUTPUT_FILE,
    bbox_inches="tight",
)

print(f"\nSaved {OUTPUT_FILE}")