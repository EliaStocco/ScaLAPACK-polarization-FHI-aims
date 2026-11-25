#!/usr/bin/env python3
"""Create a two-panel BaTiO3 scaling comparison.

The right panel reproduces the left panel of Figure 7.  The left panel plots
selected series from ``scaling_exponents_20261103``.  Change
``LEFT_PANEL_SERIES`` to select a different subset of the available data.
"""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.ticker import FixedLocator, NullLocator, ScalarFormatter
import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parent

# =============================================================================
# User-editable configuration
# =============================================================================
#
# Keep visual changes in this section whenever possible.  In particular,
# annotation positions use axes fractions: (0, 0) is the lower-left corner of
# the relevant subplot and (1, 1) is the upper-right corner.
#
# Input/output locations.  These paths assume this directory remains inside
# the FHI-aims plotting workspace.
LEFT_PANEL_DATA = ROOT / "figure7_left_panel_data.csv"
REFERENCE_DATAFRAME = ROOT / "reference_figure7_dataframe.csv"
REFERENCE_FIT = ROOT / "reference_figure7_fit.json"
STYLE_FILE = ROOT.parent / "style.mplstyle"
OUTPUT_PDF = ROOT / "Figure-7.pdf"

# Shared visual encoding.  Update these colours if the functional palette
# changes; the data, fits, annotations, and legends use the same values.
LDA_COLOR = "#1f77b4"
HSE06_COLOR = "#ff7f0e"
# Square/circle markers distinguish the 4x4x4 and 8x8x8 supercells in both
# panels and in the marker legend.
SUPERCELL_MARKERS = {4: "s", 8: "o"}

# Left-panel data selection.  Each entry is a ``series_id`` in
# ``scaling_exponents_20261103/timing_data.csv``.  The current choice uses the
# smallest available polarization grid for every functional/supercell pair.
LEFT_PANEL_SERIES = (
    "4x4x4_lda_corrected",
    "4x4x4_hse06_corrected",
    "8x8x8_lda_corrected",
    "8x8x8_hse06_corrected",
)

# Left-panel appearance.  Colour encodes the functional and marker encodes the
# supercell.  The exponent labels use a position along their fitted line and
# an offset from it (in display points):
# ``annotation_segment`` chooses its subplot (``"lower"`` or ``"upper"``).
# 4x4x4 labels are drawn in the lower subplot and 8x8x8 labels in the upper.
# Keep LDA labels below their fit and HSE06 labels above their fit.
LEFT_PANEL_STYLES = {
    "4x4x4_lda_corrected": {
        "color": LDA_COLOR,
        "marker": SUPERCELL_MARKERS[4],
        "annotation_fraction": 0.32,
        "annotation_offset_points": -10,
        "annotation_segment": "lower",
    },
    "4x4x4_hse06_corrected": {
        "color": HSE06_COLOR,
        "marker": SUPERCELL_MARKERS[4],
        "annotation_fraction": 0.35,
        "annotation_offset_points": -10,
        "annotation_segment": "lower",
    },
    "8x8x8_lda_corrected": {
        "color": LDA_COLOR,
        "marker": SUPERCELL_MARKERS[8],
        "annotation_fraction": 0.72,
        "annotation_offset_points": -10,
        "annotation_segment": "upper",
    },
    "8x8x8_hse06_corrected": {
        "color": HSE06_COLOR,
        "marker": SUPERCELL_MARKERS[8],
        "annotation_fraction": 0.70,
        "annotation_offset_points": 10,
        "annotation_segment": "upper",
    },
}

# Figure size in inches.  ``(8, 3)`` matches the Figure 7 script.
FIGSIZE = (8, 3)

# Major x ticks shown on every subplot.  Remove or add core counts here.
CORE_TICKS = (128, 256, 512, 1024, 2048)
X_MARGIN_FACTOR = 1.5

# Number and appearance of gray 1/x guide lines in each broken-axis segment.
INVERSE_GUIDE_LINE_COUNT = 10
INVERSE_GUIDE_LINE_STYLE = {
    "color": "gray",
    "alpha": 0.5,
    "linewidth": 0.5,
    "linestyle": "--",
}

# Fitted-series and broken-axis appearance.  Adjust these independently of
# the gray ideal-scaling guides above.
FIT_LINE_STYLE = "--"
LEFT_FIT_LINE_ALPHA = 0.65
RIGHT_FIT_LINE_ALPHA = 0.5
# The short diagonal strokes at the omitted y-range.  ``BREAK_MARK_SIZE`` is
# expressed as a fraction of an axes width/height.
BREAK_MARK_SIZE = 0.015
BREAK_MARK_STYLE = {"color": "black", "clip_on": False, "linewidth": 1}

# Broken-y-axis ranges.  Upper ranges span a factor of 15.  The right lower
# subplot is taller; its log range expands by the same factor as its height so
# y ∝ 1/x has the same apparent angle in all right-panel segments.
UPPER_Y_SPAN_FACTOR = 15
RIGHT_LOWER_TO_UPPER_HEIGHT_RATIO = 1.5
RIGHT_LOWER_Y_SPAN_FACTOR = UPPER_Y_SPAN_FACTOR**RIGHT_LOWER_TO_UPPER_HEIGHT_RATIO
# The paired-run subtraction yields a 6 s 4x4x4 HSE06 point at 128 cores,
# while the LDA series reaches about 208 s.
LEFT_PANEL_LOWER_YLIM = (3, 250)
LEFT_PANEL_UPPER_YLIM = (375, 375 * UPPER_Y_SPAN_FACTOR)
RIGHT_PANEL_LOWER_YLIM = (60, 60 * RIGHT_LOWER_Y_SPAN_FACTOR)
RIGHT_PANEL_UPPER_YLIM = (4000, 4000 * UPPER_Y_SPAN_FACTOR)
# The upper-right range is compressed; retain only this labelled y tick there.
RIGHT_UPPER_Y_TICKS = (10000,)

# Ideal-scaling labels.  Positions are axes fractions in their listed axes;
# ``vertical_alignment='bottom'`` makes each label sit immediately above a
# gray dashed guide line rather than crossing it.
LEFT_IDEAL_ANNOTATION = (0.6, 31, "lower")
RIGHT_IDEAL_ANNOTATION = (0.50, 13, "lower")

# Reference-panel exponent labels.  The Figure 7 data are LDA, so both use
# the LDA colour.  Move these independently of the left-panel labels above.
RIGHT_EXPONENT_ANNOTATIONS = (
    (0.48, -10, "lower", r"$m=0.94$", -0.94),
    (0.82, 10, "upper", r"$m=0.95$", -0.95),
)

# Figure layout.  The outer gap controls separation between the two panels;
# the inner gap controls the visual gap at each broken y axis.
OUTER_PANEL_WSPACE = 0.20
BROKEN_AXIS_HSPACE = 0.08
SUBPLOT_BOUNDS = {"left": 0.11, "right": 0.78, "bottom": 0.16, "top": 0.96}
Y_LABEL_POSITION = (0.05, 0.5)
Y_LABEL_TEXT = "CPU time (s)"
X_LABEL_TEXT = "n. cores"

# External legend placement, in figure fractions.  The functional legend is
# aligned with the plot top and the marker legend is directly below it.
LEGEND_X = 0.79
FUNCTIONAL_LEGEND_TOP = 0.96
MARKER_LEGEND_TOP = 0.80


def add_inverse_lines(ax, n_lines: int, **plot_kwargs) -> None:
    """Add evenly distributed 1/x guide lines within the current axis limits."""

    xmin, xmax = sorted(ax.get_xlim())
    ymin, ymax = sorted(ax.get_ylim())
    constants = np.logspace(np.log10(xmin * ymin), np.log10(xmax * ymax), n_lines)
    x = np.logspace(np.log10(xmin), np.log10(xmax), 2)

    for constant in constants:
        ax.plot(x, constant / x, **plot_kwargs)

    ax.set_xlim(xmin, xmax)
    ax.set_ylim(ymin, ymax)


def power_law_angle(ax, exponent: float) -> float:
    """Return the on-page angle of ``y ∝ x**exponent`` for *ax*."""

    xmin, xmax = ax.get_xlim()
    ymin, ymax = ax.get_ylim()
    x = np.sqrt(xmin * xmax)
    y = np.sqrt(ymin * ymax)
    scale = 1.1
    start, end = ax.transData.transform(((x, y), (x * scale, y * scale**exponent)))
    return np.degrees(np.arctan2(end[1] - start[1], end[0] - start[0]))


def add_power_law_annotation(
    ax,
    position: tuple[float, float],
    text: str,
    exponent: float,
    color: str,
    vertical_alignment: str = "center",
) -> tuple:
    """Add an annotation whose rotation is set once layout is final."""

    annotation = ax.text(
        *position,
        text,
        transform=ax.transAxes,
        ha="center",
        va=vertical_alignment,
        color=color,
    )
    return ax, annotation, exponent


def add_line_relative_annotation(
    ax,
    amplitude: float | None,
    exponent: float,
    text: str,
    color: str,
    line_fraction: float,
    offset_points: float,
) -> tuple:
    """Place rotated text at a fractional position along a power-law fit.

    ``line_fraction`` runs from the left/start of the visible fitted range
    (0) to the right/end (1).  ``offset_points`` is a signed perpendicular
    display-space distance from the line; positive values place text above the
    line on the page.
    """

    if not 0 <= line_fraction <= 1:
        raise ValueError("line_fraction must be between 0 and 1")
    xmin, xmax = sorted(ax.get_xlim())
    if amplitude is None:
        ymin, ymax = sorted(ax.get_ylim())
        amplitude = np.sqrt(xmin * xmax * ymin * ymax)
    x = xmin * (xmax / xmin) ** line_fraction
    y = amplitude * x**exponent
    angle = power_law_angle(ax, exponent)
    angle_radians = np.radians(angle)
    normal = (-np.sin(angle_radians), np.cos(angle_radians))
    annotation = ax.annotate(
        text,
        xy=(x, y),
        xycoords="data",
        xytext=(offset_points * normal[0], offset_points * normal[1]),
        textcoords="offset points",
        rotation=angle,
        rotation_mode="anchor",
        ha="center",
        va="center",
        color=color,
    )
    return ax, annotation, exponent


def fit_power_law(series: pd.DataFrame) -> tuple[float, float]:
    """Fit ``time = amplitude * cores**exponent`` in log--log space."""

    exponent, log_amplitude = np.polyfit(
        np.log(series["cores"]), np.log(series["polarization_time_s"]), 1
    )
    return float(np.exp(log_amplitude)), float(exponent)


def add_broken_y_axis_marks(upper_ax, lower_ax) -> None:
    """Visually mark the omitted interval between two vertically stacked axes."""

    upper_ax.spines["bottom"].set_visible(False)
    lower_ax.spines["top"].set_visible(False)
    upper_ax.tick_params(axis="x", which="both", bottom=False, labelbottom=False)

    size = BREAK_MARK_SIZE
    mark_kwargs = BREAK_MARK_STYLE
    upper_ax.plot((-size, size), (-size, size), transform=upper_ax.transAxes, **mark_kwargs)
    upper_ax.plot(
        (1 - size, 1 + size), (-size, size), transform=upper_ax.transAxes, **mark_kwargs
    )
    lower_ax.plot(
        (-size, size), (1 - size, 1 + size), transform=lower_ax.transAxes, **mark_kwargs
    )
    lower_ax.plot(
        (1 - size, 1 + size), (1 - size, 1 + size),
        transform=lower_ax.transAxes,
        **mark_kwargs,
    )


def plot_new_data(upper_ax, lower_ax) -> list[tuple]:
    """Plot the selected data in a left panel with a broken y axis."""

    data = pd.read_csv(LEFT_PANEL_DATA)
    data = data[data["series_id"].isin(LEFT_PANEL_SERIES)].copy()
    missing = set(LEFT_PANEL_SERIES) - set(data["series_id"])
    if missing:
        raise ValueError(f"Unknown LEFT_PANEL_SERIES entries: {sorted(missing)}")

    left_axes = {"upper": upper_ax, "lower": lower_ax}
    for ax, ylim in ((upper_ax, LEFT_PANEL_UPPER_YLIM), (lower_ax, LEFT_PANEL_LOWER_YLIM)):
        ax.set_xscale("log")
        ax.set_xlim(
            min(CORE_TICKS) / X_MARGIN_FACTOR,
            max(CORE_TICKS) * X_MARGIN_FACTOR,
        )
        ax.set_yscale("log")
        ax.set_ylim(*ylim)
    ideal_fraction, ideal_offset, ideal_segment = LEFT_IDEAL_ANNOTATION
    annotations = [
        add_line_relative_annotation(
            left_axes[ideal_segment],
            None,
            -1,
            r"ideal scalability: $m=1$",
            "gray",
            ideal_fraction,
            ideal_offset,
        )
    ]
    for series_id in LEFT_PANEL_SERIES:
        subset = data[data["series_id"] == series_id].sort_values("cores")
        style = LEFT_PANEL_STYLES[series_id]
        amplitude, exponent = fit_power_law(subset)
        x = np.logspace(np.log10(subset["cores"].min()), np.log10(subset["cores"].max()), 1000)
        for ax in (upper_ax, lower_ax):
            ax.scatter(
                subset["cores"],
                subset["polarization_time_s"],
                marker=style["marker"],
                color=style["color"],
            )
            ax.plot(
                x,
                amplitude * x**exponent,
                color=style["color"],
                linestyle=FIT_LINE_STYLE,
                alpha=LEFT_FIT_LINE_ALPHA,
            )
        annotations.append(
            add_line_relative_annotation(
                left_axes[style["annotation_segment"]],
                amplitude,
                exponent,
                rf"$m={abs(exponent):.2f}$",
                style["color"],
                style["annotation_fraction"],
                style["annotation_offset_points"],
            )
        )

    for ax, ylim in (
        (upper_ax, LEFT_PANEL_UPPER_YLIM),
        (lower_ax, LEFT_PANEL_LOWER_YLIM),
    ):
        ax.set_xscale("log")
        ax.set_yscale("log")
        ax.set_ylim(*ylim)
        ax.xaxis.set_major_locator(FixedLocator(CORE_TICKS))
        ax.xaxis.set_major_formatter(ScalarFormatter())
        ax.xaxis.set_minor_locator(NullLocator())
        add_inverse_lines(ax, INVERSE_GUIDE_LINE_COUNT, **INVERSE_GUIDE_LINE_STYLE)
    lower_ax.set_xlabel(X_LABEL_TEXT)
    add_broken_y_axis_marks(upper_ax, lower_ax)
    return annotations


def plot_figure_7_left_panel(upper_ax, lower_ax) -> list[tuple]:
    """Plot the Figure 7 reference data with a broken y axis."""

    dataframe = pd.read_csv(REFERENCE_DATAFRAME)
    dataframe = dataframe.pivot(
        index=["supercell", "ncores"], columns="calculation", values="time"
    ).reset_index()
    dataframe = dataframe.dropna(subset=["dipole", "scf"])
    dataframe["time"] = dataframe["dipole"] - dataframe["scf"]

    with REFERENCE_FIT.open() as file:
        fit = json.load(file)

    for supercell, marker in SUPERCELL_MARKERS.items():
        subset = dataframe[dataframe["supercell"] == supercell].copy()
        subset = subset.sort_values("ncores")
        x = np.logspace(
            np.log10(subset["ncores"].min()), np.log10(subset["ncores"].max()), 1000
        )
        params = fit["linear"][str(supercell)]
        for ax in (upper_ax, lower_ax):
            ax.scatter(
                subset["ncores"],
                subset["time"],
                marker=marker,
                color=LDA_COLOR,
            )
            ax.plot(
                x,
                params["A"] * x**params["m"],
                color=LDA_COLOR,
                linestyle=FIT_LINE_STYLE,
                alpha=RIGHT_FIT_LINE_ALPHA,
            )

    right_axes = {"upper": upper_ax, "lower": lower_ax}
    for ax, ylim in ((upper_ax, RIGHT_PANEL_UPPER_YLIM), (lower_ax, RIGHT_PANEL_LOWER_YLIM)):
        ax.set_xscale("log")
        ax.set_xlim(
            min(CORE_TICKS) / X_MARGIN_FACTOR,
            max(CORE_TICKS) * X_MARGIN_FACTOR,
        )
        ax.set_yscale("log")
        ax.set_ylim(*ylim)
    ideal_fraction, ideal_offset, ideal_segment = RIGHT_IDEAL_ANNOTATION
    annotations = [
        add_line_relative_annotation(
            right_axes[ideal_segment],
            None,
            -1,
            r"ideal scalability: $m=1$",
            "gray",
            ideal_fraction,
            ideal_offset,
        ),
    ]
    for fraction, offset_points, segment, text, exponent in RIGHT_EXPONENT_ANNOTATIONS:
        params = fit["linear"]["4" if segment == "lower" else "8"]
        annotations.append(
            add_line_relative_annotation(
                right_axes[segment], params["A"], params["m"], text,
                LDA_COLOR, fraction, offset_points
            )
        )

    for ax, ylim in (
        (upper_ax, RIGHT_PANEL_UPPER_YLIM),
        (lower_ax, RIGHT_PANEL_LOWER_YLIM),
    ):
        ax.set_xscale("log")
        ax.set_yscale("log")
        ax.set_ylim(*ylim)
        ax.xaxis.set_major_locator(FixedLocator(CORE_TICKS))
        ax.xaxis.set_major_formatter(ScalarFormatter())
        ax.xaxis.set_minor_locator(NullLocator())
        add_inverse_lines(ax, INVERSE_GUIDE_LINE_COUNT, **INVERSE_GUIDE_LINE_STYLE)
    # Keep only 10^4 labelled in the compressed upper-right segment.
    upper_ax.yaxis.set_major_locator(FixedLocator(RIGHT_UPPER_Y_TICKS))
    upper_ax.yaxis.set_minor_locator(NullLocator())
    lower_ax.set_xlabel(X_LABEL_TEXT)
    add_broken_y_axis_marks(upper_ax, lower_ax)
    return annotations


def add_legends(figure) -> None:
    """Add separate functional and supercell keys beside the right panel."""

    figure.legend(
        handles=(
            plt.Line2D([0], [0], color=LDA_COLOR, linestyle=FIT_LINE_STYLE, label="LDA"),
            plt.Line2D(
                [0], [0], color=HSE06_COLOR, linestyle=FIT_LINE_STYLE, label="HSE06"
            ),
        ),
        loc="upper left",
        bbox_to_anchor=(LEGEND_X, FUNCTIONAL_LEGEND_TOP),
        borderaxespad=0,
    )
    figure.legend(
        handles=(
            plt.Line2D(
                [0],
                [0],
                color="black",
                marker=SUPERCELL_MARKERS[4],
                linestyle="None",
                label="4x4x4",
            ),
            plt.Line2D(
                [0],
                [0],
                color="black",
                marker=SUPERCELL_MARKERS[8],
                linestyle="None",
                label="8x8x8",
            ),
        ),
        loc="upper left",
        bbox_to_anchor=(LEGEND_X, MARKER_LEGEND_TOP),
        borderaxespad=0,
    )


def main() -> None:
    plt.style.use(STYLE_FILE)
    plt.rcParams.update({"figure.autolayout": False})

    figure = plt.figure(figsize=FIGSIZE)
    outer_grid = figure.add_gridspec(
        1, 2, width_ratios=(1, 1), wspace=OUTER_PANEL_WSPACE
    )
    left_grid = outer_grid[0, 0].subgridspec(
        2, 1, height_ratios=(1, 1), hspace=BROKEN_AXIS_HSPACE
    )
    right_grid = outer_grid[0, 1].subgridspec(
        2,
        1,
        height_ratios=(1, RIGHT_LOWER_TO_UPPER_HEIGHT_RATIO),
        hspace=BROKEN_AXIS_HSPACE,
    )
    left_upper_ax = figure.add_subplot(left_grid[0, 0])
    left_lower_ax = figure.add_subplot(left_grid[1, 0], sharex=left_upper_ax)
    right_upper_ax = figure.add_subplot(right_grid[0, 0])
    right_lower_ax = figure.add_subplot(right_grid[1, 0], sharex=right_upper_ax)
    annotations = plot_new_data(left_upper_ax, left_lower_ax) + plot_figure_7_left_panel(
        right_upper_ax, right_lower_ax
    )
    figure.text(
        *Y_LABEL_POSITION, Y_LABEL_TEXT, ha="center", va="center", rotation="vertical"
    )
    add_legends(figure)
    figure.subplots_adjust(**SUBPLOT_BOUNDS)
    figure.canvas.draw()
    for ax, annotation, exponent in annotations:
        annotation.set_rotation(power_law_angle(ax, exponent))
    figure.savefig(OUTPUT_PDF, bbox_inches="tight")
    plt.close(figure)
    print(f"Wrote {OUTPUT_PDF}")


if __name__ == "__main__":
    main()
