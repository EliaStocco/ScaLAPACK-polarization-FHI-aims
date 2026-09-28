#!/usr/bin/env python3
"""Build the polarization k-grid convergence CSV from FHI-aims output files.

The input files are expected to be named ``aims.n=<n>.out`` in ``results/``.
For each completed calculation, the script uses the final ``Cartesian
Polarization`` line and the final ``| Total time`` accounting line.  The
polarization is converted to a cell dipole using the volume read from
``geometry.in``.
"""

from __future__ import annotations

import argparse
import csv
import re
from pathlib import Path


ELEMENTARY_CHARGE_C = 1.602176634e-19
ANGSTROM3_TO_M3 = 1.0e-30
M_TO_ANGSTROM = 1.0e10

FILE_PATTERN = re.compile(r"aims\.n=(\d+)\.out$")
FLOAT_PATTERN = r"[-+]?\d+(?:\.\d*)?(?:[Ee][-+]?\d+)?"
POLARIZATION_PATTERN = re.compile(
    rf"^\s*\| Cartesian Polarization\s+({FLOAT_PATTERN})\s+"
    rf"({FLOAT_PATTERN})\s+({FLOAT_PATTERN})\s*$",
    re.MULTILINE,
)
TIME_PATTERN = re.compile(
    rf"^\s*\| Total time\s+:\s+({FLOAT_PATTERN})\s+s\s+"
    rf"({FLOAT_PATTERN})\s+s\s*$",
    re.MULTILINE,
)


def cell_volume_angstrom3(geometry_path: Path) -> float:
    """Return the parallelepiped volume from the three lattice vectors."""
    vectors: list[tuple[float, float, float]] = []
    for line in geometry_path.read_text().splitlines():
        fields = line.split()
        if len(fields) == 4 and fields[0] == "lattice_vector":
            vectors.append(tuple(float(value) for value in fields[1:]))

    if len(vectors) != 3:
        raise ValueError(f"Expected exactly three lattice vectors in {geometry_path}")

    a, b, c = vectors
    return abs(
        a[0] * (b[1] * c[2] - b[2] * c[1])
        - a[1] * (b[0] * c[2] - b[2] * c[0])
        + a[2] * (b[0] * c[1] - b[1] * c[0])
    )


def final_match(pattern: re.Pattern[str], text: str, source: Path) -> tuple[float, ...]:
    """Read the last matching record, since FHI-aims can print intermediate ones."""
    matches = pattern.findall(text)
    if not matches:
        raise ValueError(f"Could not find the expected record in {source}")
    return tuple(float(value) for value in matches[-1])


def read_row(output_path: Path, volume_angstrom3: float) -> dict[str, int | float]:
    match = FILE_PATTERN.fullmatch(output_path.name)
    if match is None:
        raise ValueError(f"Unexpected output filename: {output_path}")
    n = int(match.group(1))
    text = output_path.read_text(errors="replace")
    px, py, pz = final_match(POLARIZATION_PATTERN, text, output_path)
    cpu_time, wall_time = final_match(TIME_PATTERN, text, output_path)

    # P (C/m^2) * V (A^3) gives C*m after converting A^3 to m^3; divide by
    # e and convert metres to Angstrom to obtain e*Angstrom.
    dipole_factor = volume_angstrom3 * ANGSTROM3_TO_M3 * M_TO_ANGSTROM / ELEMENTARY_CHARGE_C
    return {
        "polarization_kgrid_n": n,
        # n is the longitudinal sampling length in each direction-specific
        # polarization calculation; the two transverse dimensions are 8 x 8.
        "polarization_grid_x": n,
        "polarization_grid_y": n,
        "polarization_grid_z": n,
        "Px_C_per_m2": px,
        "Py_C_per_m2": py,
        "Pz_C_per_m2": pz,
        "cell_volume_A3": volume_angstrom3,
        "dipole_x_eA": px * dipole_factor,
        "dipole_y_eA": py * dipole_factor,
        "dipole_z_eA": pz * dipole_factor,
        "total_cpu_time_s": cpu_time,
        "total_wall_time_s": wall_time,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--results", type=Path, default=Path("results"), help="FHI-aims output directory")
    parser.add_argument("--geometry", type=Path, default=Path("geometry.in"), help="geometry.in file")
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("polarization_kgrid_convergence.csv"),
        help="CSV file to write",
    )
    args = parser.parse_args()

    volume = cell_volume_angstrom3(args.geometry)
    outputs = sorted(
        (path for path in args.results.glob("aims.n=*.out") if FILE_PATTERN.fullmatch(path.name)),
        key=lambda path: int(FILE_PATTERN.fullmatch(path.name).group(1)),  # type: ignore[union-attr]
    )
    if not outputs:
        raise SystemExit(f"No files matching {args.results}/aims.n=<n>.out were found")

    rows = [read_row(path, volume) for path in outputs]
    fieldnames = list(rows[0])
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(
                {
                    **row,
                    "Px_C_per_m2": f"{row['Px_C_per_m2']:.9E}",
                    "Py_C_per_m2": f"{row['Py_C_per_m2']:.9E}",
                    "Pz_C_per_m2": f"{row['Pz_C_per_m2']:.9E}",
                    "cell_volume_A3": f"{row['cell_volume_A3']:.12f}",
                    "dipole_x_eA": f"{row['dipole_x_eA']:.10f}",
                    "dipole_y_eA": f"{row['dipole_y_eA']:.10f}",
                    "dipole_z_eA": f"{row['dipole_z_eA']:.10f}",
                    "total_cpu_time_s": f"{row['total_cpu_time_s']:.3f}",
                    "total_wall_time_s": f"{row['total_wall_time_s']:.3f}",
                }
            )
    print(f"Wrote {len(rows)} rows to {args.output}")


if __name__ == "__main__":
    main()
