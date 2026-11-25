"""Reusable plotting helpers for the atom-scaling figures."""

from collections.abc import Iterable

import matplotlib.ticker as mticker


def add_external_legend(
    ax,
    *,
    x: float = 1.02,
    y: float = 1.0,
    alignment: str = "left",
    **kwargs,
):
    """Place an axis legend just outside the upper-right of the axes.

    The legend's upper-left corner is anchored at ``(x, y)`` in axes
    coordinates.  This keeps its top aligned with the top of the plotting
    area while leaving the axes itself unobstructed.
    """

    legend = ax.legend(
        loc="upper left",
        bbox_to_anchor=(x, y),
        borderaxespad=0,
        **kwargs,
    )
    legend._legend_box.align = alignment
    return legend


def configure_log_atom_axis(
    ax,
    atom_counts: Iterable[int],
    margin_factor: float = 1.5,
):
    """Configure a base-two log x-axis for selected atom counts.

    The limits are extended by the same multiplicative factor below the
    smallest count and above the largest count.  This gives equal visual
    margins on a logarithmic axis.  Major ticks are exactly *atom_counts* and
    their labels remain horizontal.

    Parameters
    ----------
    ax:
        Matplotlib axis to configure.
    atom_counts:
        Positive atom counts to display as major ticks.
    margin_factor:
        Multiplicative padding applied on both sides of the range.
    """

    ticks = sorted(set(atom_counts))
    if not ticks or any(count <= 0 for count in ticks):
        raise ValueError("atom_counts must contain positive values")
    if margin_factor <= 1:
        raise ValueError("margin_factor must be greater than 1")

    ax.set_xscale("log", base=2)
    ax.set_xlim(ticks[0] / margin_factor, ticks[-1] * margin_factor)
    ax.xaxis.set_major_locator(mticker.FixedLocator(ticks))
    ax.xaxis.set_major_formatter(mticker.FormatStrFormatter("%d"))
    ax.xaxis.set_minor_locator(mticker.NullLocator())
    ax.tick_params(axis="x", which="major", labelrotation=0)
    for label in ax.get_xticklabels():
        label.set_horizontalalignment("center")

    return ax
