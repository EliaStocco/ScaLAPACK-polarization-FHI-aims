#!/usr/bin/env python3
"""Extract FHI-aims ``vdW-like corrections`` timings from scaling outputs.

Run from this directory::

    python3 extract-vdw-timings.py

The script accepts both output layouts currently used here:
``aims.n=<cores>.out`` below a ``results`` directory and
``aims.<cores>.out`` directly below the calculation directory.  It writes
``vdw-timings.csv``.  ``cpu_time_s`` is FHI-aims' reported maximum CPU time;
``wall_time_s`` is its reported wall-clock time.
"""

import csv
import re
import sys
from pathlib import Path


OUTPUT_GLOB = "m=*/**/aims*.out"
OUTPUT_CSV = Path("vdw-timings.csv")
FILENAME_PATTERN = re.compile(r"^aims(?:\.n=|\.)(\d+)\.out$")
VDW_TIME_PATTERN = re.compile(
    r"\| Total time for vdW-like corrections\s*:\s*"
    r"([\d.]+)\s+s\s+([\d.]+)\s+s"
)


def parse_output(outfile: Path) -> dict | None:
    """Return the final vdW timing summary in *outfile*, if present."""

    filename_match = FILENAME_PATTERN.match(outfile.name)
    if not filename_match:
        return None

    timing_match = None
    with outfile.open(errors="replace") as handle:
        for line in handle:
            match = VDW_TIME_PATTERN.search(line)
            if match:
                timing_match = match

    if timing_match is None:
        return None

    return {
        "molecules": int(outfile.parts[0].removeprefix("m=")),
        "calculation": outfile.parts[1],
        "ncores": int(filename_match.group(1)),
        "cpu_time_s": float(timing_match.group(1)),
        "wall_time_s": float(timing_match.group(2)),
        "source_file": str(outfile),
    }


rows_by_run = {}
duplicate_files = 0
for outfile in sorted(set(Path(".").glob(OUTPUT_GLOB))):
    row = parse_output(outfile)
    if row is not None:
        key = (row["molecules"], row["calculation"], row["ncores"])
        existing = rows_by_run.get(key)
        if existing is None:
            rows_by_run[key] = row
        elif (existing["cpu_time_s"], existing["wall_time_s"]) == (
            row["cpu_time_s"], row["wall_time_s"]
        ):
            # The same output was copied between the old and new layouts.
            duplicate_files += 1
        else:
            raise ValueError(
                f"Conflicting vdW timings for {key}: "
                f"{existing['source_file']} and {row['source_file']}"
            )

rows = list(rows_by_run.values())

if not rows:
    raise FileNotFoundError(
        f"No vdW timing summaries found in output files matching {OUTPUT_GLOB!r}"
    )

rows.sort(key=lambda row: (row["molecules"], row["calculation"], row["ncores"]))

with OUTPUT_CSV.open("w", newline="") as handle:
    writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
    writer.writeheader()
    writer.writerows(rows)

print(f"{'molecules':>9}  {'calculation':<11}  {'cores':>5}  "
      f"{'max CPU (s)':>11}  {'wall (s)':>8}")
for row in rows:
    print(
        f"{row['molecules']:>9}  {row['calculation']:<11}  "
        f"{row['ncores']:>5}  {row['cpu_time_s']:>11.3f}  "
        f"{row['wall_time_s']:>8.3f}"
    )

print(f"\nWrote {OUTPUT_CSV}")
if duplicate_files:
    print(
        f"Skipped {duplicate_files} duplicate output file(s) with identical timings.",
        file=sys.stderr,
    )
