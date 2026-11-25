#!/usr/bin/env python3
"""Adapt corrected component timings to the original Figure 7 plot schema."""

from __future__ import annotations

import csv
from pathlib import Path


HERE = Path(__file__).resolve().parent
SOURCE = HERE / "component_timing_data.csv"
OUTPUT = HERE / "figure7_component_data.csv"


def main() -> None:
    with SOURCE.open(newline="") as handle:
        source_rows = list(csv.DictReader(handle))
    rows = [
        {
            "series_id": f"{row['supercell']}_{row['functional'].lower()}_corrected",
            "cores": row["cores"],
            "polarization_time_s": row["polarization_seconds"],
            "fourier_interpolation_time_s": row["fourier_seconds"],
            "dipole_matrix_time_s": row["dipole_matrix_seconds"],
            "dipole_term_time_s": row["dipole_term_seconds"],
            "berry_term_time_s": row["berry_term_seconds"],
        }
        for row in source_rows
    ]
    fields = list(rows[0])
    with OUTPUT.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    print(f"Wrote {OUTPUT}")


if __name__ == "__main__":
    main()
