#!/usr/bin/env python3

"""Plot polarization cost relative to SCF convergence cost."""

import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import pandas as pd

from plot import BASE, COLORS, DATA_FILE, STYLE_FILE


OUTPUT_FILE = BASE / "polarization-vs-convergence.pdf"


# ---------------------------------------------------------
# Load data
# ---------------------------------------------------------
df = pd.read_csv(DATA_FILE)

required = {
    "nodes",
    "atoms",
    "method",
    "polarization_time",
    "converge_time",
}

missing = required - set(df.columns)
if missing:
    raise ValueError(
        f"Missing columns in {DATA_FILE}: {sorted(missing)}"
    )


# ---------------------------------------------------------
# Select two-node ScaLAPACK calculations
# ---------------------------------------------------------
df = df[
    (df["nodes"] == 2)
    & (df["method"] == "scalapack")
].copy()

df = df.dropna(
    subset=[
        "atoms",
        "polarization_time",
        "converge_time",
    ]
)

df = df[
    (df["atoms"] > 0)
    & (df["polarization_time"] > 0)
    & (df["converge_time"] > 0)
]

df = df.sort_values("atoms")

if df.empty:
    raise RuntimeError(
        "No valid two-node ScaLAPACK data found"
    )


# ---------------------------------------------------------
# Relative cost
# ---------------------------------------------------------
df["relative_cost"] = (
    df["polarization_time"]
    / df["converge_time"]
)


# ---------------------------------------------------------
# Style
# ---------------------------------------------------------
if STYLE_FILE.exists():
    plt.style.use(STYLE_FILE)


# ---------------------------------------------------------
# Plot
# ---------------------------------------------------------
fig, ax = plt.subplots(figsize=(3, 3))

ax.plot(
    df["atoms"],
    df["relative_cost"],
    color=COLORS["scalapack"],
    marker="o",
    linewidth=1.2,
    markersize=4,
)


# ---------------------------------------------------------
# Log-log axes
# ---------------------------------------------------------
ax.set_xscale("log", base=2)
ax.set_yscale("log")

ax.set_xlabel("n. atoms")
ax.set_ylabel(
    r"$t_{\mathrm{pol}}/t_{\mathrm{SCF}}$"
)


# ---------------------------------------------------------
# Equal-cost reference
# ---------------------------------------------------------
ax.axhline(
    1.0,
    color="gray",
    linestyle="--",
    linewidth=0.8,
    alpha=0.7,
)


# ---------------------------------------------------------
# X ticks
# ---------------------------------------------------------
xticks = sorted(df["atoms"].unique())

ax.xaxis.set_major_locator(
    mticker.FixedLocator(xticks)
)

ax.xaxis.set_major_formatter(
    mticker.FormatStrFormatter("%d")
)

ax.xaxis.set_minor_locator(
    mticker.NullLocator()
)

ax.tick_params(
    axis="x",
    which="major",
    length=4,
    labelrotation=35,
)

for label in ax.get_xticklabels():
    label.set_horizontalalignment("right")


# ---------------------------------------------------------
# Print values
# ---------------------------------------------------------
print()
print("atoms   t_pol / t_SCF")
print("---------------------")

for _, row in df.iterrows():
    print(
        f"{int(row['atoms']):5d}   "
        f"{row['relative_cost']:.6f}"
    )


# ---------------------------------------------------------
# Save
# ---------------------------------------------------------
plt.tight_layout()

plt.savefig(
    OUTPUT_FILE,
    bbox_inches="tight",
)

print(f"\nSaved {OUTPUT_FILE}")