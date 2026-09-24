#!/usr/bin/env python3
"""Plot the vdW-like-corrections timings extracted by extract-vdw-timings.py.

Examples::

    python3 plot-vdw-timings.py
    python3 plot-vdw-timings.py --metric wall --output vdw-wall-time.pdf
"""

import argparse
import csv
from collections import defaultdict
from pathlib import Path

import matplotlib.pyplot as plt


METRICS = {
    "cpu": ("cpu_time_s", "Maximum CPU time (s)"),
    "wall": ("wall_time_s", "Wall-clock time (s)"),
}
CALCULATION_STYLE = {
    "scf": {"marker": "o", "color": "#1f77b4", "label": "SCF"},
    "dipole": {"marker": "s", "color": "#ff7f0e", "label": "Dipole"},
}


def read_rows(filename: Path) -> list[dict]:
    with filename.open(newline="") as handle:
        rows = list(csv.DictReader(handle))
    if not rows:
        raise ValueError(f"{filename} contains no timing data")
    for row in rows:
        row["molecules"] = int(row["molecules"])
        row["ncores"] = int(row["ncores"])
        row["cpu_time_s"] = float(row["cpu_time_s"])
        row["wall_time_s"] = float(row["wall_time_s"])
    return rows


parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--input", type=Path, default=Path("vdw-timings.csv"))
parser.add_argument("--output", type=Path, default=Path("vdw-timings.pdf"))
parser.add_argument("--metric", choices=METRICS, default="cpu")
args = parser.parse_args()

rows = read_rows(args.input)
value_column, ylabel = METRICS[args.metric]
data = defaultdict(list)
for row in rows:
    data[(row["molecules"], row["calculation"])].append(row)

molecules = sorted({row["molecules"] for row in rows})
fig, axes = plt.subplots(1, len(molecules), figsize=(4.0 * len(molecules), 3.2),
                         sharey=True, squeeze=False)

for ax, molecule_count in zip(axes[0], molecules):
    for calculation in ("scf", "dipole"):
        subset = sorted(data.get((molecule_count, calculation), []),
                        key=lambda row: row["ncores"])
        if not subset:
            continue
        style = CALCULATION_STYLE.get(calculation, {"marker": "o", "label": calculation})
        ax.plot(
            [row["ncores"] for row in subset],
            [row[value_column] for row in subset],
            linewidth=1.2,
            **style,
        )

    ax.set_title(f"{molecule_count} water molecules")
    ax.set_xscale("log", base=2)
    ax.set_xticks(sorted({row["ncores"] for row in rows if row["molecules"] == molecule_count}))
    ax.set_xlabel("MPI ranks")
    ax.grid(axis="y", alpha=0.3)

axes[0][0].set_ylabel(ylabel)
axes[0][-1].legend(title="Calculation")
fig.suptitle("FHI-aims: vdW-like corrections", y=1.02)
fig.tight_layout()
fig.savefig(args.output, bbox_inches="tight")
print(f"Wrote {args.output}")
