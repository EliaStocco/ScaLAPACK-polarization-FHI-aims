"""Plot the HSE06 dipole-only scaling results.

Run ``extract.py`` and ``fit-dataframe.py`` before this script.  The plot is
saved as ``water-HSE06.pdf`` in the current directory.
"""

import json

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.ticker import FixedLocator, NullLocator, ScalarFormatter


plt.style.use("../../style.mplstyle")

XTICKS = [128, 256, 512, 1024]
YTICKS = [25, 50, 100, 200]


def add_inverse_lines(ax, n_lines, **plot_kwargs):
    """Add guides with ideal inverse-core scaling."""

    xmin, xmax = sorted(ax.get_xlim())
    ymin, ymax = sorted(ax.get_ylim())
    constants = np.logspace(np.log10(xmin * ymin), np.log10(xmax * ymax), n_lines)
    x = np.logspace(np.log10(xmin), np.log10(xmax), 2)

    for constant in constants:
        ax.plot(x, constant / x, **plot_kwargs)

    ax.set_xlim(xmin, xmax)
    ax.set_ylim(ymin, ymax)


df = pd.read_csv("dataframe.csv")
df = df.pivot(index="ncores", columns="calculation", values="time").reset_index()
df["time"] = df["dipole"] - df["scf"]
df = df.sort_values("ncores")

with open("fit.json") as handle:
    fit = json.load(handle)

fig, ax = plt.subplots(figsize=(6, 3.4))

ax.scatter(df["ncores"], df["time"], marker="o", label="HSE06")

x = np.logspace(np.log10(df["ncores"].min()), np.log10(df["ncores"].max()), 1000)
params = fit["linear"]
ax.plot(x, params["A"] * x ** params["m"], linestyle="--", alpha=0.5)

ax.text(
    0.5,
    0.75,
    "ideal scalability: $m=1$",
    transform=ax.transAxes,
    rotation=-22,
    ha="center",
    va="center",
    color="gray",
)
ax.text(
    0.5,
    0.42,
    rf"$m={params['m']:.2f}$",
    transform=ax.transAxes,
    rotation=-16,
    ha="center",
    va="center",
    color="#1f77b4",
)

ax.set_xscale("log")
ax.set_yscale("log")
ax.set_xlabel("n. cores")
ax.set_ylabel("CPU time (s)")
ax.legend(loc="lower left")

ax.xaxis.set_major_locator(FixedLocator(XTICKS))
ax.xaxis.set_major_formatter(ScalarFormatter())
ax.xaxis.set_minor_locator(NullLocator())
ax.yaxis.set_major_locator(FixedLocator(YTICKS))
ax.yaxis.set_major_formatter(ScalarFormatter())
ax.yaxis.set_minor_locator(NullLocator())
ax.set_ylim(25, 200)

add_inverse_lines(
    ax,
    n_lines=20,
    color="gray",
    alpha=0.5,
    linewidth=0.5,
    linestyle="--",
)

plt.tight_layout()
plt.savefig("water-HSE06.pdf", bbox_inches="tight")
