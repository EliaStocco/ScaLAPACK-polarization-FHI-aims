#!/usr/bin/env python3
"""Extract BLACS grid dimensions from the HSE06 scaling outputs.

Run from this directory::

    python3 extract-blacs-grid.py

The script writes ``blacs-grids.csv`` and prints a compact summary.  An aspect
ratio of one is square; larger values quantify the deviation from square.
"""

import csv
import re
from pathlib import Path


OUTPUT_FILES = "*-HSE06/results/aims.n=*.out"
OUTPUT_CSV = Path("blacs-grids.csv")

MPI_TASKS_PATTERN = re.compile(r"\bUsing\s+(\d+) parallel tasks\.")
BLACS_GRID_PATTERN = re.compile(
    r"K-point:\s*(\d+)\s+Tasks:\s*(\d+)\s+split into\s*"
    r"(\d+)\s+X\s+(\d+)\s+BLACS grid"
)


def extract_grids(outfile):
    """Return every BLACS grid declared in one FHI-aims output file."""

    mpi_tasks = None
    grids = []

    with outfile.open() as handle:
        for line in handle:
            match = MPI_TASKS_PATTERN.search(line)
            if match:
                mpi_tasks = int(match.group(1))

            match = BLACS_GRID_PATTERN.search(line)
            if match:
                kpoint, grid_tasks, nprow, npcol = map(int, match.groups())
                aspect_ratio = max(nprow, npcol) / min(nprow, npcol)
                grids.append(
                    {
                        "file": str(outfile),
                        "calculation": outfile.parts[0].removesuffix("-HSE06"),
                        "mpi_tasks": mpi_tasks,
                        "kpoint": kpoint,
                        "blacs_tasks": grid_tasks,
                        "nprow": nprow,
                        "npcol": npcol,
                        "grid": f"{nprow} x {npcol}",
                        "aspect_ratio": aspect_ratio,
                        "shape": "square" if nprow == npcol else "skewed",
                        "task_count_matches": grid_tasks == nprow * npcol,
                    }
                )

    return grids


rows = []
for outfile in sorted(Path(".").glob(OUTPUT_FILES)):
    rows.extend(extract_grids(outfile))

if not rows:
    raise FileNotFoundError(f"No BLACS grids found in {OUTPUT_FILES!r}")

rows.sort(key=lambda row: (row["calculation"], row["mpi_tasks"], row["kpoint"]))

fieldnames = list(rows[0])
with OUTPUT_CSV.open("w", newline="") as handle:
    writer = csv.DictWriter(handle, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(rows)

print(f"{'calculation':<12} {'MPI ranks':>9} {'BLACS ranks':>11} {'grid':>10} "
      f"{'aspect':>7}  shape")
for row in rows:
    print(
        f"{row['calculation']:<12} {row['mpi_tasks']:>9} "
        f"{row['blacs_tasks']:>11} {row['grid']:>10} "
        f"{row['aspect_ratio']:>7.2f}  {row['shape']}"
    )

print(f"\nWrote {OUTPUT_CSV}")
