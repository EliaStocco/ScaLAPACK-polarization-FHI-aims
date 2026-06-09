import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker

plt.style.use("../style.mplstyle")


# -----------------------------
# Load data
# -----------------------------
df = pd.read_csv("dataframe.csv")

df = df.sort_values(["method", "supercell"])

df["atoms"] = 2*np.power(df["supercell"],3)


# -----------------------------
# Plot setup
# -----------------------------
fig, ax = plt.subplots(figsize=(3, 2))

colors = {
    "lapack": "#1f77b4",
    "scalapack": "#ff7f0e",
}

labels = {
    "lapack": "LAPACK",
    "scalapack": "ScaLAPACK",
}


# -----------------------------
# Plot each method
# -----------------------------
for method in ["lapack", "scalapack"]:

    sub = df[df["method"] == method].sort_values("supercell")

    if sub.empty:
        continue
    
    ax.scatter(
        sub["atoms"],
        sub["time"],
        color=colors[method],
        label=labels[method],
    )
    

    ax.plot(
        sub["atoms"],
        sub["time"],
        linewidth=1.2,
        alpha=0.6,
        color=colors[method]
    )


# -----------------------------
# Log scaling (like your other figures)
# -----------------------------
ax.set_xscale("log", base=2)
ax.set_yscale("log", base=2)

# -----------------------------
# Labels
# -----------------------------
ax.set_xlabel("n. atoms")
ax.set_ylabel("CPU time (s)")


# -----------------------------
# Ticks (clean supercell numbers)
# -----------------------------
xticks = sorted(df["atoms"].unique())

ax.xaxis.set_major_locator(mticker.FixedLocator(xticks))
ax.xaxis.set_major_formatter(mticker.FormatStrFormatter("%d"))

ax.tick_params(axis="x", which="minor", length=3)
ax.tick_params(axis="x", which="major", length=4)


# -----------------------------
# Legend styling
# -----------------------------
legend = ax.legend(loc="best")

legend.get_frame().set_facecolor("white")
legend.get_frame().set_edgecolor("black")
legend.get_frame().set_alpha(1.0)


# -----------------------------
# Layout + save
# -----------------------------
plt.tight_layout()
plt.savefig("comparison.pdf", bbox_inches="tight")