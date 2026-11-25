#!/usr/bin/env python3
"""Extract wall-clock polarization-component timers for the Figure 5 comparison."""

from __future__ import annotations

import argparse
import re
from pathlib import Path

import pandas as pd


HERE = Path(__file__).resolve().parent
SCALAPACK_DIRECTORY = HERE.parent / "dipole" / "scalapack"
OUTPUT_FILE = HERE / "component_timing_data.csv"

COMPONENTS = {
    "dipole_matrix_time_s": "dipole matrix",
    "dipole_term_time_s": "dipole term",
    "berry_term_time_s": "berry term",
    "fourier_interpolation_time_s": "Fourier interpolated EV solution",
}


def wall_time(pattern: str, text: str, path: Path) -> float:
    """Return the wall-clock column of a unique timing row."""

    matches = re.findall(pattern, text, flags=re.MULTILINE)
    if len(matches) != 1:
        raise ValueError(f"Expected one match for {pattern!r} in {path}; found {len(matches)}")
    return float(matches[0])


def parse_output(path: Path) -> dict[str, float]:
    """Read the wall-clock times from an FHI-aims output file."""

    text = path.read_text(errors="replace")
    timer_start = text.rfind("Wannier center evolution                                :")
    if timer_start == -1:
        raise ValueError(f"Cannot locate the Wannier-center timer block in {path}")
    timer_block = text[timer_start:]
    values = {
        "polarization_time_s": wall_time(
            r"^\s*\| Total Time\s+:\s+[0-9.]+\s+([0-9.]+)\s*$",
            timer_block,
            path,
        )
    }
    for column, label in COMPONENTS.items():
        values[column] = wall_time(
            rf"^\s*\| Total Time for {re.escape(label)}\s+:\s+[0-9.]+\s+([0-9.]+)\s*$",
            text,
            path,
        )
    return values


def collect_scalapack() -> list[dict[str, float | int | str]]:
    rows = []
    for path in sorted(SCALAPACK_DIRECTORY.glob("aims.*.out")):
        match = re.fullmatch(r"aims\.(\d+)\.out", path.name)
        if match is None:
            continue
        rows.append({"method": "ScaLAPACK", "ncores": int(match.group(1)), **parse_output(path)})
    return rows


def collect_lapack(directory: Path) -> list[dict[str, float | int | str]]:
    rows = []
    for path in sorted(directory.glob("n=*/results/aims.n=*.out")):
        match = re.fullmatch(r"aims\.n=(\d+)\.out", path.name)
        if match is None:
            continue
        rows.append({"method": "LAPACK", "ncores": int(match.group(1)), **parse_output(path)})
    return rows


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("lapack_directory", type=Path, help="Downloaded lapack-rerun-recompiled-executable directory")
    arguments = parser.parse_args()
    rows = collect_scalapack() + collect_lapack(arguments.lapack_directory)
    data = pd.DataFrame(rows).sort_values(["method", "ncores"])
    data.to_csv(OUTPUT_FILE, index=False, float_format="%.6f")
    print(f"Wrote {OUTPUT_FILE} with {len(data)} timing rows")


if __name__ == "__main__":
    main()
