#!/usr/bin/env python3
"""Extract corrected polarization-component wall times from raw FHI-aims logs."""

from __future__ import annotations

import csv
import re
from pathlib import Path


HERE = Path(__file__).resolve().parent
TIMINGS = HERE / "timing_data.csv"
OUTPUT = HERE / "component_timing_data.csv"
PATTERNS = {
    "dipole_matrix_seconds": r"\| Total Time for dipole matrix\s+:",
    "dipole_term_seconds": r"\| Total Time for dipole term\s+:",
    "berry_term_seconds": r"\| Total Time for berry term\s+:",
    "fourier_seconds": r"\| Total Time for Fourier interpolated EV solution\s+:",
}


def last_wall_time(text: str, pattern: str) -> float:
    matches = []
    for line in text.splitlines():
        if re.search(pattern, line, re.IGNORECASE):
            numbers = re.findall(r"[-+]?\d+(?:\.\d+)?", line.split(":", 1)[-1])
            if numbers:
                matches.append(float(numbers[-1]))
    if not matches:
        raise ValueError(f"Timer not found: {pattern}")
    return matches[-1]


def main() -> None:
    with TIMINGS.open(newline="") as handle:
        rows = list(csv.DictReader(handle))
    output_rows = []
    for row in rows:
        path = HERE / row["dipole_file"]
        text = path.read_text(errors="replace")
        result = dict(row)
        for name, pattern in PATTERNS.items():
            result[name] = f"{last_wall_time(text, pattern):.6f}"
        output_rows.append(result)
    with OUTPUT.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(output_rows[0]))
        writer.writeheader()
        writer.writerows(output_rows)
    print(f"Wrote {OUTPUT}")


if __name__ == "__main__":
    main()
