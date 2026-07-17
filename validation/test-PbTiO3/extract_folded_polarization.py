#!/usr/bin/env python3
"""Extract and unwrap the z polarization along the PbTiO3 distortion path."""

from __future__ import annotations

import argparse
import csv
import math
import re
from pathlib import Path


GEOMETRY_RE = re.compile(r"aims\.n=(\d+)\.out$")
P0_RE = re.compile(r"P0=\s*([-+]?\d*\.?\d+(?:[Ee][-+]?\d+)?)\s+C/m\^2")


def parse_output(path: Path) -> tuple[float, float]:
    """Return Cartesian Pz and the Pz polarization-quantum magnitude (C/m^2)."""
    cartesian_z = None
    quanta = []

    for line in path.read_text().splitlines():
        if "Cartesian Polarization" in line:
            fields = line.split()
            cartesian_z = float(fields[-1])
        match = P0_RE.search(line)
        if match:
            quanta.append(float(match.group(1)))

    if cartesian_z is None:
        raise ValueError(f"No Cartesian Polarization line in {path}")
    # There are two P0 entries per directive (Berry and dipole); directive 3 is entries 5/6.
    if len(quanta) < 5:
        raise ValueError(f"Could not find the directive-3 polarization quantum in {path}")
    return cartesian_z, abs(quanta[4])


def nearest_integer(value: float) -> int:
    """Round to the nearest integer without Python's ties-to-even behaviour."""
    return math.floor(value + 0.5) if value >= 0 else math.ceil(value - 0.5)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "root", nargs="?", type=Path, default=Path(__file__).parent,
        help="Directory containing LDA/, PBEsol/, and HSE06/ (default: script directory).",
    )
    parser.add_argument(
        "-o", "--output", type=Path,
        help="Output CSV path (default: <root>/folded_polarization.csv).",
    )
    args = parser.parse_args()
    output = args.output or args.root / "folded_polarization.csv"

    known_functionals = ("LDA", "PBEsol", "HSE06")
    directories = {path.name: path for path in args.root.iterdir() if path.is_dir()}
    functional_dirs = [directories.pop(name) for name in known_functionals if name in directories]
    functional_dirs.extend(sorted(directories.values(), key=lambda path: path.name))

    rows = []
    for functional_dir in functional_dirs:
        files = []
        for path in (functional_dir / "results").glob("aims.n=*.out"):
            match = GEOMETRY_RE.search(path.name)
            if match:
                files.append((int(match.group(1)), path))
        if not files:
            continue

        previous_folded = None
        for geometry, path in sorted(files):
            raw, quantum = parse_output(path)
            branch_shift = 0 if previous_folded is None else nearest_integer((previous_folded - raw) / quantum)
            folded = raw + branch_shift * quantum
            previous_folded = folded
            rows.append({
                "functional": functional_dir.name,
                "geometry": geometry,
                "raw_polarization_z_C_per_m2": f"{raw:.12f}",
                "polarization_quantum_C_per_m2": f"{quantum:.9f}",
                "branch_shift_quanta": branch_shift,
                "folded_polarization_z_C_per_m2": f"{folded:.12f}",
                "source_file": str(path.relative_to(functional_dir)),
            })

    fields = list(rows[0]) if rows else []
    if not rows:
        raise SystemExit(f"No results/aims.n=*.out files found below {args.root}")
    with output.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)

    for functional in sorted({row["functional"] for row in rows}):
        functional_rows = [row for row in rows if row["functional"] == functional]
        quanta = ", ".join(
            f"n={row['geometry']}: {float(row['polarization_quantum_C_per_m2']):.9f}"
            for row in functional_rows
        )
        print(f"{functional}: Pz quanta (C/m^2): {quanta}")
        values = [float(row["folded_polarization_z_C_per_m2"])
                  for row in functional_rows]
        print(f"{functional}: P(geometry 9) - P(geometry 0) = {values[-1] - values[0]:.9f} C/m^2")


if __name__ == "__main__":
    main()
