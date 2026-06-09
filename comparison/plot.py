import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
from matplotlib.offsetbox import OffsetImage, AnnotationBbox
import matplotlib.image as mpimg

def add_inverse_lines(ax, n_lines, **plot_kwargs):
    """
    Add exactly n_lines of y = C/x, filling the plot from corner to corner.
    """
    xmin, xmax = ax.get_xlim()
    ymin, ymax = ax.get_ylim()

    xmin, xmax = min(xmin, xmax), max(xmin, xmax)
    ymin, ymax = min(ymin, ymax), max(ymin, ymax)

    # Corner-touching limits (this is the key correction)
    C_min = ymin*xmin
    C_max = ymax*xmax

    # Log-spaced constants to evenly fill the plot
    C_values = np.logspace(np.log10(C_min), np.log10(C_max), n_lines)

    x = np.logspace(np.log10(xmin), np.log10(xmax), 2)

    for C in C_values:
        y = C/x
        ax.plot(x, y, **plot_kwargs)
        
    ax.set_xlim(xmin, xmax)
    ax.set_ylim(ymin, ymax)

plt.style.use("../style.mplstyle")

df = pd.read_csv("dataframe.csv")

pivot = df.pivot_table(
    index=["ncores", "method"],
    columns="calculation",
    values="time"
).reset_index()

pivot["diff"] = pivot["dipole"] - pivot["scf"]

colors = {
    "LAPACK": "#1f77b4",
    "ScaLAPACK": "#ff7f0e"
}

plt.figure(figsize=(4, 2.3))
ax = plt.gca()

for method in pivot["method"].unique():
    sub = pivot[pivot["method"] == method].sort_values("ncores")

    ax.plot(
        sub["ncores"],
        sub["diff"],
        color=colors.get(method, "black"),
        linewidth=1.0,
        alpha=0.5
    )

    ax.scatter(
        sub["ncores"],
        sub["diff"],
        color=colors.get(method, "black"),
        label=method,
        zorder=3
    )

# ---- PNG image ----
img = mpimg.imread("MgO.png")

imagebox = OffsetImage(img, zoom=0.07)
ab = AnnotationBbox(imagebox, (900, 600), frameon=False)
ax.add_artist(ab)

# ---- Log scales ----
ax.set_xscale("log", base=2)
ax.set_yscale("log")

ax.set_xlabel("n. cores")
ax.set_ylabel("CPU time (s)")

# ---- PRIMARY x ticks ----
ax.xaxis.set_major_locator(mticker.FixedLocator([128, 256, 512, 1024, 2024]))
ax.xaxis.set_major_formatter(mticker.FormatStrFormatter("%d"))

# ---- SECONDARY (minor) x ticks ----
# ax.xaxis.set_minor_locator(mticker.LogLocator(base=2, subs=np.linspace(1.1, 1.9, 5), numticks=100))
# ax.xaxis.set_minor_formatter(mticker.NullFormatter())

ax.tick_params(axis="x", which="minor", length=3)
ax.tick_params(axis="x", which="major", length=4)

add_inverse_lines(ax,20,**{"color":"gray","alpha":0.5,"linewidth":0.5,"linestyle":"--"})

ax.text(
    0.28, 0.6,
    r"ideal scaling",
    transform=ax.transAxes,
    rotation=-50,      # angle in degrees
    ha="center",
    fontsize=8,
    va="center",
    color="gray"
)

# Legend styling
legend = plt.legend()
legend.get_frame().set_facecolor("white")
legend.get_frame().set_edgecolor("black")
legend.get_frame().set_alpha(1.0)

plt.tight_layout()
plt.savefig("scaling.pdf", bbox_inches="tight")