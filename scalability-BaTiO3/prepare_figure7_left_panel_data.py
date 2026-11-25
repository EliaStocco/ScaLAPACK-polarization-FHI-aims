#!/usr/bin/env python3
"""Adapt corrected timings to the original Figure 7 left-panel schema."""

from __future__ import annotations

import csv
from pathlib import Path


HERE = Path(__file__).resolve().parent
SOURCE = HERE / "timing_data.csv"
OUTPUT = HERE / "figure7_left_panel_data.csv"


def main() -> None:
    with SOURCE.open(newline="") as handle:
        rows = list(csv.DictReader(handle))
    output_rows = [
        {
            "series_id": f"{row['supercell']}_{row['functional'].lower()}_corrected",
            "cores": row["cores"],
            "polarization_time_s": row["polarization_seconds"],
        }
        for row in rows
    ]
    with OUTPUT.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(output_rows[0]))
        writer.writeheader()
        writer.writerows(output_rows)
    print(f"Wrote {OUTPUT}")


if __name__ == "__main__":
    main()
