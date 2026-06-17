import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# Read the data
df = pd.read_csv("dataframe.csv")

fig, axes = plt.subplots(1, 2, figsize=(12, 5), sharex=True)

# ------------------------
# Helper: polynomial fit
# ------------------------
def add_polyfit(ax, x, y, label, deg=3):
    coeffs = np.polyfit(x, y, deg)
    poly = np.poly1d(coeffs)

    x_fit = np.linspace(min(x), max(x), 200)
    y_fit = poly(x_fit)

    ax.plot(x_fit, y_fit, linestyle="--", label=f"{label} fit (deg {deg})")

    return coeffs


# ========================
# Plot TIME
# ========================
ax = axes[0]

for method in df["method"].unique():
    subset = df[df["method"] == method].sort_values("supercell")

    x = subset["supercell"].values
    y = subset["time_s"].values

    ax.plot(x, y, marker="o", label=method)

    # polynomial fit
    add_polyfit(ax, x, y, method)

ax.set_xlabel("supercell size")
ax.set_ylabel("Time (s)")
ax.set_title("Execution Time")
ax.grid(True)
ax.legend()


# ========================
# Plot MEMORY
# ========================
ax = axes[1]

for method in df["method"].unique():
    subset = df[df["method"] == method].sort_values("supercell")

    x = subset["supercell"].values
    y = subset["memory_mb"].values

    ax.plot(x, y, marker="o", label=method)

    # polynomial fit
    add_polyfit(ax, x, y, method)

ax.set_xlabel("supercell size")
ax.set_ylabel("Memory per node (MB)")
ax.set_title("Memory Usage")
ax.grid(True)
ax.legend()

plt.tight_layout()
plt.savefig("performance_scaling.png", dpi=300)
plt.show()