#!/usr/bin/env python3

"""Plot the two-node polarization timings without the speedup panel."""

import matplotlib.pyplot as plt
import matplotlib.ticker as mticker

from plot import BASE, COLORS, DATA_FILE, METHOD_LABELS, STYLE_FILE, load_data

OUTPUT_FILE = BASE / "scaling-4-nodes.pdf"


def plot(rows):
    fig, ax = plt.subplots(figsize=(3,3))
    fig.set_layout_engine(None)
    fig.set_tight_layout(False)

    for method in ("lapack", "scalapack"):
        subset = sorted(
            (
                row
                for row in rows
                if row["method"] == method and row["nodes"] == 4
            ),
            key=lambda row: row["atoms"],
        )
        if not subset:
            continue

        ax.plot(
            [row["atoms"] for row in subset],
            [row["polarization_time"] / 3600.0 for row in subset],
            color=COLORS[method],
            marker="o",
            linewidth=1.2,
            markersize=4,
            label=f"{METHOD_LABELS[method]}",
        )

    ax.set_xscale("log", base=2)
    ax.set_yscale("log", base=2)
    ax.set_ylim(1.0 / 4500.0, 30.0)
    ax.set_xlabel("n. atoms")
    ax.set_ylabel("CPU time (h)")

    time_ticks = [1.0 / 3600.0, 1.0 / 60.0, 1.0, 24.0]
    time_labels = ["1 s", "1 m", "1 h", "1 day"]
    ax.yaxis.set_major_locator(mticker.FixedLocator(time_ticks))
    ax.yaxis.set_major_formatter(mticker.FixedFormatter(time_labels))

    xticks = sorted(
        {row["atoms"] for row in rows if row["nodes"] == 2}
    )
    ax.xaxis.set_major_locator(mticker.FixedLocator(xticks))
    ax.xaxis.set_major_formatter(mticker.FormatStrFormatter("%d"))
    ax.tick_params(axis="x", which="minor", length=3)
    ax.tick_params(axis="x", which="major", length=4, labelrotation=35)
    for label in ax.get_xticklabels():
        label.set_horizontalalignment("right")

    legend = ax.legend(loc="best")
    legend.get_frame().set_facecolor("white")
    legend.get_frame().set_edgecolor("black")
    legend.get_frame().set_alpha(1.0)

    fig.subplots_adjust(left=0.16, right=0.98, bottom=0.20, top=0.97)
    return fig


def main():
    if STYLE_FILE.exists():
        plt.style.use(STYLE_FILE)
    plt.rcParams["figure.autolayout"] = False

    rows = load_data(DATA_FILE)
    if not rows:
        raise RuntimeError(f"No data found in {DATA_FILE}")

    figure = plot(rows)
    figure.savefig(OUTPUT_FILE, bbox_inches="tight")
    print(f"Saved {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
