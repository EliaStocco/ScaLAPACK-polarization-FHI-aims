import pandas as pd
import matplotlib.pyplot as plt
plt.style.use("../style.mplstyle")

df = pd.read_csv("dataframe.csv")
df = df.sort_values(by="atoms")

fig, axes = plt.subplots(2,1,figsize=(3.5,2.5),sharex=True)


ax = axes[0]
ax.scatter(df["atoms"],df["memory"],color="red")
ax.plot(df["atoms"],df["memory"],color="red",alpha=0.5,linewidth=1,linestyle="--")
# ax.set_title("memory [MB]")
ax.text(
    0.03, 0.91, "memory (MB)",
    transform=ax.transAxes,
    bbox=dict(boxstyle="square,pad=0.3", facecolor="white", edgecolor="black"),
    ha="left", va="top"
)
ax.set_xlim(0,None)
ax.set_ylim(0,None)

ax = axes[1]
ax.scatter(df["atoms"],df["time"],color="blue",s=10)
ax.plot(df["atoms"],df["time"],color="blue",alpha=0.5,linewidth=1,linestyle="--")
ax.set_xlabel("n. atoms")
# ax.set_title("CPU time [s]")
ax.text(
    0.03, 0.91, "CPU time (s)",
    transform=ax.transAxes,
    bbox=dict(boxstyle="square,pad=0.3", facecolor="white", edgecolor="black"),
    ha="left", va="top"
)
ax.set_xlim(0,None)
ax.set_ylim(0,None)

# fig.subplots_adjust(hspace=0)
plt.tight_layout()
plt.savefig("memory.pdf",bbox_inches="tight")


pass