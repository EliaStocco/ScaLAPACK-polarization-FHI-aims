import json

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import matplotlib.image as mpimg
from matplotlib.offsetbox import OffsetImage, AnnotationBbox
from matplotlib.ticker import FixedLocator, NullLocator, ScalarFormatter

plt.style.use("../style.mplstyle")


MOLECULES = [4,8]
MARKERS = ["o", "s"]

XTICKS = [128, 256, 512, 768, 1024,2048]


def add_inverse_lines(ax, n_lines, **plot_kwargs):
    """Add n_lines lines of ideal 1/x scaling."""

    xmin, xmax = sorted(ax.get_xlim())
    ymin, ymax = sorted(ax.get_ylim())

    constants = np.logspace(
        np.log10(xmin * ymin),
        np.log10(xmax * ymax),
        n_lines,
    )

    x = np.logspace(np.log10(xmin), np.log10(xmax), 2)

    for c in constants:
        ax.plot(x, c / x, **plot_kwargs)

    ax.set_xlim(xmin, xmax)
    ax.set_ylim(ymin, ymax)


# Load data
df = pd.read_csv("dataframe.csv")

# -----------------------------
# Convert to wide format
# -----------------------------
df_wide = df.pivot(
    index=["supercell", "ncores"],
    columns="calculation",
    values="time"
).reset_index()

df_wide = df_wide.dropna(subset=["dipole", "scf"])

# -----------------------------
# Compute difference
# -----------------------------
df_wide["time"] = df_wide["dipole"] - df_wide["scf"]

with open("fit.json") as f:
    fit = json.load(f)


# Create figure
fig, ax = plt.subplots()

for marker, mol in zip(MARKERS, MOLECULES):

    subset = df_wide[df_wide["supercell"] == mol]
    
    if subset.empty:
        continue
    
    # IMPORTANT: compute difference here
    subset = subset.copy()
    subset["time"] = subset["dipole"] - subset["scf"]

    subset = subset.sort_values("ncores")

    # Data points
    ax.scatter(
        subset["ncores"],
        subset["time"],
        marker=marker,
        label=f"{mol}x{mol}x{mol}",
    )

    # Fit
    params = fit["linear"][str(mol)]

    x = np.logspace(
        np.log10(subset["ncores"].min()),
        np.log10(subset["ncores"].max()),
        1000,
    )

    y = params["A"] * x ** params["m"]

    ax.plot(
        x,
        y,
        linestyle="--",
        alpha=0.5,
    )


# Axes formatting
#ax.set_title("Liquid water, intermediate basis set, revPBE0+D3")

img = mpimg.imread("BaTiO3.4x4x4.png")
imagebox = OffsetImage(img, zoom=0.04)
ab = AnnotationBbox(
    imagebox,
    (0.1, 0.65),              # position
    xycoords='axes fraction',  # IMPORTANT: decouples from data limits
    frameon=False
)
ax.add_artist(ab)

img = mpimg.imread("BaTiO3.8x8x8.png")
imagebox = OffsetImage(img, zoom=0.08)
ab = AnnotationBbox(
    imagebox,
    (0.85, 0.6),              # position
    xycoords='axes fraction',  # IMPORTANT: decouples from data limits
    frameon=False
)
ax.add_artist(ab)

# ax.text(
#     0.132, 0.33,
#     r"$y = Ax^{-m}$",
#     transform=ax.transAxes,
#     ha="right",
#     va="top",
#     bbox=dict(
#         boxstyle="round",
#         facecolor="white",
#         edgecolor="black"
#     )
# )

ax.text(
    0.5, 0.48,
    r"ideal scalability: $m=1$",
    transform=ax.transAxes,
    rotation=-18,      # angle in degrees
    ha="center",
    va="center",
    color="gray"
)

ax.text(
    0.4, 0.31,
    r"$m=0.94$",
    transform=ax.transAxes,
    rotation=-18,      # angle in degrees
    ha="center",
    va="center",
    color="#1f77b4"
)

ax.text(
    0.85, 0.92,
    r"$m=0.95$",
    transform=ax.transAxes,
    rotation=-18,      # angle in degrees
    ha="center",
    va="center",
    color="#ff7f0e"
)

ax.set_xscale("log")
ax.set_yscale("log")

ax.set_xlabel("n. cores")
ax.set_ylabel("CPU time (s)")

legend = ax.legend(
    title="Supercell:",
    loc="lower left",
)
legend._legend_box.align = "left"

ax.xaxis.set_major_locator(FixedLocator(XTICKS))
ax.xaxis.set_major_formatter(ScalarFormatter())
ax.xaxis.set_minor_locator(NullLocator())

# Ideal scaling guides
add_inverse_lines(
    ax,
    n_lines=20,
    color="gray",
    alpha=0.5,
    linewidth=0.5,
    linestyle="--",
)

plt.tight_layout()
plt.savefig("BaTiO3.supercell.pdf", bbox_inches="tight")