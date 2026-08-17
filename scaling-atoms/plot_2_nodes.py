#!/usr/bin/env python3

"""Plot the two-node polarization timings."""

import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import matplotlib.image as mpimg
import pandas as pd
import numpy as np
from matplotlib.offsetbox import OffsetImage, AnnotationBbox

from plot import BASE, COLORS, DATA_FILE, METHOD_LABELS, STYLE_FILE

OUTPUT_FILE = BASE / "scaling-2-nodes.pdf"


# Load data
df = pd.read_csv(DATA_FILE)

required = {
    "nodes",
    "supercell",
    "atoms",
    "method",
    "scf_time",
    "dipole_time",
    "polarization_time",
}

missing = required - set(df.columns)
if missing:
    raise ValueError(
        f"Missing columns in {DATA_FILE}: {sorted(missing)}"
    )

if df.empty:
    raise RuntimeError(f"No data found in {DATA_FILE}")


# Use the same plotting style
if STYLE_FILE.exists():
    plt.style.use(STYLE_FILE)


# -----------------------------
# Select two-node calculations
# -----------------------------
df = df[df["nodes"] == 2].copy()
df = df.sort_values(["method", "atoms"])

df = df[df["atoms"] != 686]


# -----------------------------
# Create figure
# -----------------------------
fig, ax = plt.subplots(figsize=(3,3))


# -----------------------------
# Plot timings
# -----------------------------
for method in ("lapack", "scalapack"):

    subset = df[df["method"] == method]

    if subset.empty:
        continue

    ax.plot(
        subset["atoms"],
        subset["polarization_time"] / 3600.0,
        color=COLORS[method],
        marker="o",
        linewidth=1.2,
        markersize=4,
        label=METHOD_LABELS[method],
    )


# -----------------------------
# Axes
# -----------------------------
ax.set_xscale("log", base=2)
ax.set_yscale("log", base=2)

ax.set_ylim(None, 24.0)

ax.set_xlabel("n. atoms")
ax.set_ylabel("CPU time")


# -----------------------------
# Y ticks
# -----------------------------
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


# -----------------------------
# X ticks
# -----------------------------
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


# -----------------------------
# Legend
# -----------------------------
legend = ax.legend(loc="upper left")

legend.get_frame().set_facecolor("white")
legend.get_frame().set_edgecolor("black")
legend.get_frame().set_alpha(1.0)

# -----------------------------
# Images
# -----------------------------
img = mpimg.imread("supercell.2.png")
imagebox = OffsetImage(img, zoom=0.015)
ab = AnnotationBbox(
    imagebox,
    (0.08, 0.2),              # position
    xycoords='axes fraction',  # IMPORTANT: decouples from data limits
    frameon=False
)
ax.add_artist(ab)

img = mpimg.imread("supercell.4.png")
imagebox = OffsetImage(img, zoom=0.03)
ab = AnnotationBbox(
    imagebox,
    (0.45, 0.55),              # position
    xycoords='axes fraction',  # IMPORTANT: decouples from data limits
    frameon=False
)
ax.add_artist(ab)


img = mpimg.imread("supercell.8.png")
imagebox = OffsetImage(img, zoom=0.05)
ab = AnnotationBbox(
    imagebox,
    (0.7, 0.2),              # position
    xycoords='axes fraction',  # IMPORTANT: decouples from data limits
    frameon=False
)
ax.add_artist(ab)

ax.annotate(
    "",
    xy=(1000, 3.0),
    xytext=(500, 0.005),
    arrowprops=dict(
        arrowstyle="->",
        connectionstyle="arc3,rad=0.1",
        linewidth=0.5,
        alpha=0.8
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
        alpha=0.8
    ),
)
def add_lines(ax, n_lines, **plot_kwargs):
    """Add n_lines lines with y = c*x scaling."""

    xmin, xmax = sorted(ax.get_xlim())
    ymin, ymax = sorted(ax.get_ylim())

    constants = np.logspace(
        np.log10(ymin / xmax),
        np.log10(ymax / xmin),
        n_lines,
    )

    x = np.logspace(np.log10(xmin), np.log10(xmax), 2)

    for c in constants:
        ax.plot(x, c * x, **plot_kwargs)

    ax.set_xlim(xmin, xmax)
    ax.set_ylim(ymin, ymax)




ax.text(
    0.3, 0.71,
    r"ideal scaling: $m=1$",
    transform=ax.transAxes,
    rotation=19,      # angle in degrees
    ha="center",
    va="center",
    color="gray"
)

# -----------------------------
# Plot timings + power-law fits
# -----------------------------
fit = {}
for method in ("lapack", "scalapack"):

    subset = df[df["method"] == method]

    if subset.empty:
        continue

    xdata = subset["atoms"].to_numpy(dtype=float)
    ydata = (subset["polarization_time"] / 3600.0).to_numpy(dtype=float)

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

    # Smooth fitted curve
    xfit = np.logspace(
        np.log10(xdata.min()),
        np.log10(xdata.max()),
        200,
    )
    yfit = A * xfit**m
    fit[method] = m

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

m = np.round(fit["lapack"],1)
ax.text(
    0.3, 0.33,
    f"$m={m}$",
    transform=ax.transAxes,
    rotation=40,      # angle in degrees
    ha="center",
    va="center",
    color="#1f77b4"
)

m = np.round(fit["scalapack"],1)
ax.text(
    0.6, 0.4,
    f"$m={m}$",
    transform=ax.transAxes,
    rotation=33,      # angle in degrees
    ha="center",
    va="center",
    color="#ff7f0e"
)

# -----------------------------
# Layout and output
# -----------------------------
plt.tight_layout()


# Ideal scaling guides
add_lines(
    ax,
    n_lines=20,
    color="gray",
    alpha=0.5,
    linewidth=0.5,
    linestyle="--",
)

plt.savefig(
    OUTPUT_FILE,
    bbox_inches="tight",
)

print(f"Saved {OUTPUT_FILE}")