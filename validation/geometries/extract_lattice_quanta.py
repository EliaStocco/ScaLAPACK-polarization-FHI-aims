#!/usr/bin/env python3
"""Write lattice parameters and conventional vector quanta for validation cells."""

from __future__ import annotations

import argparse
import csv
import math
import re
from pathlib import Path
from typing import Iterator


ELEMENTARY_CHARGE_C = 1.602176634e-19
ANGSTROM2_TO_M2 = 1.0e-20
LATTICE_RE = re.compile(r'\bLattice="([^"]+)"')
Vector = tuple[float, float, float]
Cell = tuple[Vector, Vector, Vector]


def dot(left: Vector, right: Vector) -> float:
    return sum(a * b for a, b in zip(left, right))


def cross(left: Vector, right: Vector) -> Vector:
    return (
        left[1] * right[2] - left[2] * right[1],
        left[2] * right[0] - left[0] * right[2],
        left[0] * right[1] - left[1] * right[0],
    )


def norm(vector: Vector) -> float:
    return math.sqrt(dot(vector, vector))


def angle_degrees(left: Vector, right: Vector) -> float:
    cosine = dot(left, right) / (norm(left) * norm(right))
    return math.degrees(math.acos(max(-1.0, min(1.0, cosine))))


def parse_geometry_in(path: Path) -> Cell:
    vectors = []
    with path.open(encoding="utf-8", errors="replace") as handle:
        for line in handle:
            fields = line.split()
            if fields and fields[0].lower() == "lattice_vector":
                if len(fields) < 4:
                    raise ValueError(f"Malformed lattice_vector in {path}: {line.rstrip()}")
                vectors.append(tuple(float(value) for value in fields[1:4]))

    if len(vectors) != 3:
        raise ValueError(f"Expected three lattice vectors in {path}, found {len(vectors)}")
    return tuple(vectors)  # type: ignore[return-value]


def parse_extxyz(path: Path) -> Iterator[tuple[int, Cell]]:
    with path.open(encoding="utf-8", errors="replace") as handle:
        frame = 0
        while True:
            atom_count_line = handle.readline()
            if not atom_count_line:
                return
            if not atom_count_line.strip():
                continue
            try:
                atom_count = int(atom_count_line)
            except ValueError as error:
                raise ValueError(
                    f"Expected an atom count for frame {frame} in {path}"
                ) from error

            comment = handle.readline()
            match = LATTICE_RE.search(comment)
            if not match:
                raise ValueError(f"No Lattice attribute for frame {frame} in {path}")
            values = [float(value) for value in match.group(1).split()]
            if len(values) != 9:
                raise ValueError(
                    f"Expected nine Lattice values for frame {frame} in {path}"
                )
            cell = tuple(
                tuple(values[index:index + 3]) for index in range(0, 9, 3)
            )

            for _ in range(atom_count):
                if not handle.readline():
                    raise ValueError(f"Incomplete frame {frame} in {path}")

            yield frame, cell  # type: ignore[misc]
            frame += 1


def cell_values(cell: Cell) -> dict[str, str]:
    first, second, third = cell
    volume = abs(dot(first, cross(second, third)))
    if math.isclose(volume, 0.0, abs_tol=1e-15):
        raise ValueError("Cell has zero volume")

    # The conventional polarization-quantum vector is e R_i / Omega.  Report
    # its magnitude for each direct lattice vector R_i.  FHI-aims instead
    # prints its projection along reciprocal direction i as P0.
    quantum_factor = ELEMENTARY_CHARGE_C / ANGSTROM2_TO_M2
    return {
        "a_A": f"{norm(first):.12g}",
        "b_A": f"{norm(second):.12g}",
        "c_A": f"{norm(third):.12g}",
        "alpha_deg": f"{angle_degrees(second, third):.12g}",
        "beta_deg": f"{angle_degrees(first, third):.12g}",
        "gamma_deg": f"{angle_degrees(first, second):.12g}",
        "volume_A3": f"{volume:.12g}",
        "polarization_quantum_P1_C_m2": f"{quantum_factor * norm(first) / volume:.12g}",
        "polarization_quantum_P2_C_m2": f"{quantum_factor * norm(second) / volume:.12g}",
        "polarization_quantum_P3_C_m2": f"{quantum_factor * norm(third) / volume:.12g}",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "root", nargs="?", type=Path, default=Path(__file__).parent,
        help="geometry directory to scan recursively (default: script directory)",
    )
    parser.add_argument(
        "-o", "--output", type=Path,
        help=("output CSV path (default: "
              "<root>/lattice_parameters_and_polarization_quanta.csv)"),
    )
    args = parser.parse_args()
    if not args.root.is_dir():
        parser.error(f"directory does not exist: {args.root}")
    output = args.output or args.root / "lattice_parameters_and_polarization_quanta.csv"

    rows = []
    for path in sorted(args.root.rglob("*")):
        if not path.is_file():
            continue
        relative_path = path.relative_to(args.root)
        if path.name == "geometry.in":
            rows.append({
                "source_file": str(relative_path),
                "frame": "",
                **cell_values(parse_geometry_in(path)),
            })
        elif path.suffix.lower() == ".extxyz":
            for frame, cell in parse_extxyz(path):
                rows.append({
                    "source_file": str(relative_path),
                    "frame": str(frame),
                    **cell_values(cell),
                })

    if not rows:
        raise SystemExit(f"No geometry.in or .extxyz geometries found below {args.root}")

    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    print(f"Wrote {len(rows)} geometries to {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
