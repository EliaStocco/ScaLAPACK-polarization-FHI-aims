from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np
import pandas as pd


def add_inverse_lines(ax, n_lines=20, **kwargs):
    """
    Add n_lines of y = C / x guide curves (ideal inverse scaling)
    and restore axis limits at the end.
    """

    xmin, xmax = sorted(ax.get_xlim())
    ymin, ymax = sorted(ax.get_ylim())
    
    print(xmin, xmax)
    print(ymin, ymax)

    # safety for log plots
    # if xmin <= 0 or ymin <= 0:
    #     return

    # save original limits
    xlim = (xmin, xmax)
    ylim = (ymin, ymax)

    x = np.logspace(np.log10(xmin), np.log10(xmax), 200)

    c_min = xmin * ymin
    c_max = xmax * ymax

    for c in np.logspace(np.log10(c_min), np.log10(c_max), n_lines):
        ax.plot(x, c / x, **kwargs)

    # restore limits (important after plotting)
    ax.set_xlim(xlim)
    ax.set_ylim(ylim)
    
# -----------------------------
# Settings
# -----------------------------
BASE = Path(__file__).resolve().parent
ROOT = BASE.parent
STYLE_FILE = ROOT / "style.mplstyle"
DATA_FILE = BASE / "dataframe.csv"
OUTPUT_FILE = Path(__file__).resolve().parent / "Figure-5.pdf"

COLORS = {
    "LAPACK": "#1f77b4",
    "ScaLAPACK": "#ff7f0e",
}
METHOD_LABELS = {
    "LAPACK": r"\texttt{LAPACK}",
    "ScaLAPACK": r"\texttt{ScaLAPACK}",
}


# -----------------------------
# Load data
# -----------------------------
def load_data(path):
    df = pd.read_csv(path)

    required = {"calculation", "method", "ncores", "time", "peak_memory_mb"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Missing columns: {missing}")

    df = df.sort_values(["method", "calculation", "ncores"])
    return df


# -----------------------------
# Plot
# -----------------------------
def plot(df):
    fig, (ax1, ax2) = plt.subplots(
        2,
        1,
        figsize=(4, 4),
        sharex=True,
        gridspec_kw={"height_ratios": [2, 1]},
    )

    df = df[df["ncores"] <= 1024]

    # =========================================================
    # TOP: CPU time (dipole only, as before: dipole - scf)
    # =========================================================
    dip = df[df["calculation"] == "dipole"].set_index(["method", "ncores"])
    scf = df[df["calculation"] == "scf"].set_index(["method", "ncores"])

    common = dip.index.intersection(scf.index)

    dip = dip.loc[common]
    scf = scf.loc[common]

    diff = dip["time"] - scf["time"]

    diff = diff.reset_index()

    for method, sub in diff.groupby("method"):
        sub = sub.sort_values("ncores")
        color = COLORS.get(method, "black")
        high_core_lapack = (method == "LAPACK") & (sub["ncores"] > 16)
        facecolors = np.where(high_core_lapack, "white", color)

        ax1.plot(
            sub["ncores"],
            sub["time"],
            color=color,
            alpha=0.7,
        )

        ax1.scatter(
            sub["ncores"],
            sub["time"],
            facecolors=facecolors,
            edgecolors=color,
            linewidths=1.0,
            label=METHOD_LABELS[method],
            zorder=3,
        )

    ax1.set_yscale("log")
    ax1.set_ylabel("CPU time (s)")
    ax1.legend(loc="lower left", framealpha=1.0)

    # ax1.text(
    #     0.13,
    #     0.25,
    #     "ideal scalability",
    #     transform=ax1.transAxes,
    #     rotation=-60,
    #     fontsize=8,
    #     color="gray",
    # )
    
    ax1.set_xlim(7,1200)
    xticks = [8, 16, 32, 64, 128, 256, 512, 1024]
    ax1.xaxis.set_major_locator(mticker.FixedLocator(xticks))
    ax1.xaxis.set_major_formatter(mticker.FormatStrFormatter("%d"))
    
    # Display the logarithmic CPU-time ticks directly in seconds.
    yticks = [100, 200, 500, 1000]

    ax1.yaxis.set_major_locator(mticker.FixedLocator(yticks))
    ax1.yaxis.set_major_formatter(mticker.FixedFormatter([str(tick) for tick in yticks]))

    # add_inverse_lines(
    #     ax1,
    #     n_lines=20,
    #     color="gray",
    #     alpha=0.5,
    #     linewidth=0.5,
    #     linestyle="--",
    # )

    # =========================================================
    # BOTTOM: dipole peak memory for the same core counts as the CPU-time plot
    # =========================================================
    mem = (
        df[df["calculation"] == "dipole"]
        .set_index(["method", "ncores"])
        .loc[common]
        .reset_index()
    )

    for method, sub in mem.groupby("method"):
        sub = sub.sort_values("ncores")
        color = COLORS.get(method, "black")
        high_core_lapack = (method == "LAPACK") & (sub["ncores"] > 16)
        facecolors = np.where(high_core_lapack, "white", color)

        ax2.plot(
            sub["ncores"],
            sub["peak_memory_mb"]/1000,
            color=color,
            alpha=0.7,
        )

        ax2.scatter(
            sub["ncores"],
            sub["peak_memory_mb"]/1000,
            facecolors=facecolors,
            edgecolors=color,
            linewidths=1.0,
            zorder=3,
        )

    ax2.set_xscale("log", base=2)
    ax2.set_xlabel("n. cores")
    ax2.set_ylabel("peak memory (GB)")

    xticks = [8, 16, 32, 64, 128, 256, 512, 1024]
    ax2.xaxis.set_major_locator(mticker.FixedLocator(xticks))
    ax2.xaxis.set_major_formatter(mticker.FormatStrFormatter("%d"))
    
    ax2.set_ylim(0,2)
    
    # ax2.grid(
    #     True,
    #     color="gray",
    #     alpha=0.5,
    #     linewidth=0.5,
    #     linestyle="--",
    # )

    fig.subplots_adjust(left=0.20, right=0.98, bottom=0.14, top=0.98, hspace=0.12)
    return fig


# -----------------------------
# Main
# -----------------------------
def main():
    if Path(STYLE_FILE).exists():
        plt.style.use(STYLE_FILE)

    df = load_data(DATA_FILE)

    fig = plot(df)

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUTPUT_FILE)


if __name__ == "__main__":
    main()
