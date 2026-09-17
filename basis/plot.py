import json
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import matplotlib.image as mpimg
from matplotlib.offsetbox import OffsetImage, AnnotationBbox
from matplotlib.ticker import FixedLocator, NullLocator, ScalarFormatter

plt.style.use("../style.mplstyle")

XTICKS = [128, 256, 512, 1024]

# -----------------------------
# Helper: inverse scaling guides
# -----------------------------
def add_inverse_lines(ax, n_lines, **plot_kwargs):
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


def power_law_angle(ax, exponent):
    """Return the on-page angle of y ∝ x**exponent for the current axes."""

    xmin, xmax = ax.get_xlim()
    ymin, ymax = ax.get_ylim()
    x = np.sqrt(xmin * xmax)
    y = np.sqrt(ymin * ymax)
    scale = 1.1
    start, end = ax.transData.transform(((x, y), (x * scale, y * scale ** exponent)))
    return np.degrees(np.arctan2(end[1] - start[1], end[0] - start[0]))


# -----------------------------
# Load + reshape data
# -----------------------------
df = pd.read_csv("dataframe.csv")

df = df.pivot_table(
    index=["basis", "ncores"],
    columns="calculation",
    values="time",
    aggfunc="mean"
).reset_index()

df["time"] = df["dipole"] - df["scf"]


# -----------------------------
# Load fit
# -----------------------------
with open("fit.json") as f:
    fit = json.load(f)


# -----------------------------
# Plot
# -----------------------------
fig, ax = plt.subplots(figsize=(6,3))

basis_sets = ["light", "intermediate", "tight"]
markers = ["o", "s", "D"]

for basis, marker in zip(basis_sets, markers):

    sub = df[df["basis"] == basis].sort_values("ncores")

    if sub.empty:
        continue

    # -------------------------
    # Data points
    # -------------------------
    ax.scatter(
        sub["ncores"],
        sub["time"],
        marker=marker,
        label=basis,
    )

    # -------------------------
    # Fit curve: y = A x^m
    # -------------------------
    params = fit["linear"][basis]

    x_fit = np.logspace(
        np.log10(sub["ncores"].min()),
        np.log10(sub["ncores"].max()),
        500,
    )

    y_fit = params["A"] * x_fit ** params["m"]

    ax.plot(
        x_fit,
        y_fit,
        linestyle="--",
        alpha=0.6,
    )


# -----------------------------
# Log scales
# -----------------------------
ax.set_xscale("log")
ax.set_yscale("log")


# -----------------------------
# Labels
# -----------------------------
ax.set_xlabel("n. cores")
ax.set_ylabel("CPU time (s)")
# ax.set_title("Basis set scaling comparison")


# -----------------------------
# Ideal scaling guides (1/x)
# -----------------------------
add_inverse_lines(
    ax,
    n_lines=20,
    color="gray",
    alpha=0.5,
    linewidth=0.5,
    linestyle="--",
)

# -----------------------------
# Legend styling
# -----------------------------
legend = ax.legend(
    title="species:",
    loc="upper left",
    bbox_to_anchor=(1.02, 1),
    borderaxespad=0,
)
legend._legend_box.align = "left"

# ax.text(
#     0.98, 0.95,
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

annotations = []

annotations.append((ax.text(
    0.4, 0.2,
    r"ideal scalability: $m=1$",
    transform=ax.transAxes,
    ha="center",
    va="center",
    color="gray"
), -1))

annotations.append((ax.text(
    0.5, 0.32,
    r"$m=0.82$",
    transform=ax.transAxes,
    ha="center",
    va="center",
    color="#1f77b4"
), fit["linear"]["light"]["m"]))

annotations.append((ax.text(
    0.5, 0.51,
    r"$m=0.87$",
    transform=ax.transAxes,
    ha="center",
    va="center",
    color="#ff7f0e"
), fit["linear"]["intermediate"]["m"]))

annotations.append((ax.text(
    0.5, 0.77,
    r"$m=0.72$",
    transform=ax.transAxes,
    ha="center",
    va="center",
    color="#2ca02c"
), fit["linear"]["tight"]["m"]))

img = mpimg.imread("BaTiO3.4x4x4.png")
imagebox = OffsetImage(img, zoom=0.04)
ab = AnnotationBbox(
    imagebox,
    (0.78, 0.8),              # position
    xycoords='axes fraction',  # IMPORTANT: decouples from data limits
    frameon=False
)
ax.add_artist(ab)

ax.xaxis.set_major_locator(FixedLocator(XTICKS))
ax.xaxis.set_major_formatter(ScalarFormatter())
ax.xaxis.set_minor_locator(NullLocator())

# -----------------------------
# Save
# -----------------------------
plt.tight_layout()
fig.canvas.draw()
for annotation, exponent in annotations:
    annotation.set_rotation(power_law_angle(ax, exponent))
plt.savefig("basis.pdf", bbox_inches="tight")
