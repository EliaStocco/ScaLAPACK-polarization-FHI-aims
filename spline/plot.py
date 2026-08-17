#!/usr/bin/env python3

"""Plot polarization along [111] relative to the last available k-grid."""

import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import pandas as pd
import numpy as np
from pathlib import Path


BASE = Path(__file__).resolve().parent
plt.style.use("../style.mplstyle")

COLORS = {
    "yes": "#ff7f0e",
    "no": "#1f77b4" ,
}

DATA_FILE = BASE / "dataframe.csv"
OUTPUT_FILE = BASE / "spline.pdf"


# ---------------------------------------------------------
# Load data
# ---------------------------------------------------------
df = pd.read_csv(DATA_FILE)
df = df[df['k_grid'] >= 2]

required = {
    "spline",
    "k_grid",
    "polarization_x",
    "polarization_y",
    "polarization_z",
}

missing = required - set(df.columns)

if missing:
    raise ValueError(
        f"Missing columns in {DATA_FILE}: {sorted(missing)}"
    )

if df.empty:
    raise RuntimeError(f"No data found in {DATA_FILE}")


# ---------------------------------------------------------
# Clean and sort data
# ---------------------------------------------------------
df = df.copy()

df = df[
    (df["k_grid"] > 0)
    & df["polarization_x"].notna()
    & df["polarization_y"].notna()
    & df["polarization_z"].notna()
]

df = df.sort_values(
    ["spline", "k_grid"]
)


# ---------------------------------------------------------
# Polarization along [111]
# ---------------------------------------------------------
df["polarization_111"] = (
    df["polarization_x"]
    + df["polarization_y"]
    + df["polarization_z"]
) / np.sqrt(3.0)


# ---------------------------------------------------------
# Difference relative to last available spline value
# ---------------------------------------------------------
df_spline = df[
    df["spline"].str.lower() == "yes"
].copy()

if df_spline.empty:
    raise RuntimeError(
        "No spline data available to define the reference."
    )

reference = (
    df_spline
    .sort_values("k_grid")
    .iloc[-1]["polarization_111"]
)

df["delta_polarization_111"] = np.abs(
    df["polarization_111"] - reference
)

print(
    f"Reference P_[111] = {reference:.10e} "
    f"at k_grid = {int(df_spline['k_grid'].max())}"
)


# ---------------------------------------------------------
# Create figure
# ---------------------------------------------------------
fig, ax = plt.subplots(
    figsize=(3, 2.5),
)


# ---------------------------------------------------------
# Data
# ---------------------------------------------------------
for spline, label in (
    ("no", "no spline"),
    ("yes", "spline"),
):

    subset = df[
        df["spline"].str.lower() == spline
    ]

    if subset.empty:
        continue

    ax.plot(
        subset["k_grid"],
        1000*subset["delta_polarization_111"],
        color=COLORS[spline],
        marker=".",
        linewidth=1.2,
        markersize=6,
        label=label,
    )


# ---------------------------------------------------------
# Axes
# ---------------------------------------------------------
ax.set_xscale(
    "log",
    base=2,
)
# ax.set_yscale(
#     "log",
#     base=10,
# )

ax.set_xlabel(
    r"perpendicular nscf $\mathbf{k}$-grid"
)

ax.set_ylabel(
    r"$\Delta P$ (mC/$m^2$)"
)

ax.axhline(
    0.0,
    color="gray",
    linewidth=0.5,
    linestyle="--",
)

ax.axvline(
    8,
    color="gray",
    linewidth=0.5,
    linestyle="--",
)

# ---------------------------------------------------------
# SCF k-grid annotation
# ---------------------------------------------------------
ax.annotate(
    r"scf $\mathbf{k}$-grid",
    xy=(8, 0.5),
    xycoords=("data", "axes fraction"),
    xytext=(0.6, 0.6),
    textcoords="axes fraction",
    arrowprops=dict(
        arrowstyle="->",
        connectionstyle="arc3,rad=0.15",
        linewidth=0.5,
        color="gray",
    ),
    ha="center",
    va="center",
)
# ---------------------------------------------------------
# X ticks
# ---------------------------------------------------------
xticks = sorted(
    df["k_grid"].unique()
)

ax.xaxis.set_major_locator(
    mticker.FixedLocator(xticks)
)

ax.xaxis.set_major_formatter(
    mticker.FormatStrFormatter("%d")
)

ax.xaxis.set_minor_locator(
    mticker.NullLocator()
)


# ---------------------------------------------------------
# Legend
# ---------------------------------------------------------
legend = ax.legend(
    loc="upper right",
)

legend.get_frame().set_facecolor("white")
legend.get_frame().set_edgecolor("black")
legend.get_frame().set_alpha(1.0)


# ---------------------------------------------------------
# Layout and output
# ---------------------------------------------------------
fig.subplots_adjust(
    left=0.20,
    right=0.98,
    bottom=0.15,
    top=0.98,
)

plt.savefig(
    OUTPUT_FILE,
    bbox_inches="tight",
)

print(f"Saved {OUTPUT_FILE}")