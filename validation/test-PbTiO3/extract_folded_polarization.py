#!/usr/bin/env python3
"""Extract and unwrap polarization along the PbTiO3 distortion path."""

from __future__ import annotations

import argparse
import csv
import math
import re
from pathlib import Path


GEOMETRY_RE = re.compile(r"aims\.n=(\d+)\.out$")
P0_RE = re.compile(r"P0=\s*([-+]?\d*\.?\d+(?:[Ee][-+]?\d+)?)\s+C/m\^2")
FULL_POLARIZATION_RE = re.compile(
    r"Directive\s+([123])\b.*?yields the full polarization\s*:\s*"
    r"([-+]?\d*\.?\d+(?:[Ee][-+]?\d+)?)"
)
ELEMENTARY_CHARGE_C = 1.602176634e-19
ANGSTROM2_TO_M2 = 1.0e-20
Vector = tuple[float, float, float]
Cell = tuple[Vector, Vector, Vector]


def parse_output(
    path: Path,
) -> tuple[Vector, Vector, Vector, Cell]:
    """Return Cartesian P, FHI projections/quanta, and the direct cell."""
    cartesian = None
    directive_polarizations = [None, None, None]
    lattice_vectors = []
    quanta = []

    for line in path.read_text().splitlines():
        if "Cartesian Polarization" in line:
            fields = line.split()
            cartesian = tuple(float(value) for value in fields[-3:])
        full_polarization_match = FULL_POLARIZATION_RE.search(line)
        if full_polarization_match:
            direction = int(full_polarization_match.group(1)) - 1
            directive_polarizations[direction] = float(full_polarization_match.group(2))
        fields = line.split()
        if fields and fields[0].lower() == "lattice_vector" and len(fields) >= 4:
            lattice_vectors.append(tuple(float(value) for value in fields[1:4]))
        match = P0_RE.search(line)
        if match:
            quanta.append(float(match.group(1)))

    if cartesian is None:
        raise ValueError(f"No Cartesian Polarization line in {path}")
    if any(value is None for value in directive_polarizations):
        raise ValueError(f"Could not find all three full directive polarizations in {path}")
    if len(lattice_vectors) < 3:
        raise ValueError(f"Could not find all three direct lattice vectors in {path}")
    # There are two P0 entries per directive (Berry and dipole), in directive order.
    if len(quanta) < 6:
        raise ValueError(f"Could not find all three polarization quanta in {path}")
    cell = tuple(lattice_vectors[-3:])
    # Recompute these from the full-precision cell.  The P0 values printed by
    # FHI-aims can be rounded to only six decimal places.
    directive_quanta = projected_quantum_magnitudes(cell)
    return (
        cartesian,
        tuple(directive_polarizations),
        directive_quanta,
        cell,
    )


def nearest_integer(value: float) -> int:
    """Round to the nearest integer without Python's ties-to-even behaviour."""
    return math.floor(value + 0.5) if value >= 0 else math.ceil(value - 0.5)


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


def projected_quantum_magnitudes(cell: Cell) -> Vector:
    """Return FHI projected quanta e/|a_j x a_k| from a full-precision cell."""
    face_areas = (
        norm(cross(cell[1], cell[2])),
        norm(cross(cell[2], cell[0])),
        norm(cross(cell[0], cell[1])),
    )
    return tuple(
        ELEMENTARY_CHARGE_C / ANGSTROM2_TO_M2 / area
        for area in face_areas
    )


def conventional_representation(
    projected_polarizations: Vector,
    projected_quanta: Vector,
    cell: Cell,
) -> tuple[Vector, Vector, Vector, Vector]:
    """Return reduced values, vector-quantum magnitudes, components, and Cartesian P."""
    volume = abs(dot(cell[0], cross(cell[1], cell[2])))
    if math.isclose(volume, 0.0, abs_tol=1e-15):
        raise ValueError("Cell has zero volume")

    quantum_factor = ELEMENTARY_CHARGE_C / ANGSTROM2_TO_M2 / volume
    quantum_vectors = tuple(
        tuple(quantum_factor * component for component in lattice_vector)
        for lattice_vector in cell
    )
    quantum_magnitudes = tuple(norm(vector) for vector in quantum_vectors)
    reduced = tuple(
        polarization / quantum
        for polarization, quantum in zip(projected_polarizations, projected_quanta)
    )
    conventional_components = tuple(
        value * quantum
        for value, quantum in zip(reduced, quantum_magnitudes)
    )
    cartesian = tuple(
        sum(
            reduced[direction] * quantum_vectors[direction][component]
            for direction in range(3)
        )
        for component in range(3)
    )
    return reduced, quantum_magnitudes, conventional_components, cartesian


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
    folded_directive_rows = []
    for functional_dir in functional_dirs:
        files = []
        for path in (functional_dir / "results").glob("aims.n=*.out"):
            match = GEOMETRY_RE.search(path.name)
            if match:
                files.append((int(match.group(1)), path))
        if not files:
            continue

        previous_folded_directives = None
        for geometry, path in sorted(files):
            (
                raw_cartesian,
                directive_polarizations,
                directive_quanta,
                cell,
            ) = parse_output(path)
            if previous_folded_directives is None:
                branch_shifts = (0, 0, 0)
                folded_directives = directive_polarizations
            else:
                branch_shifts = tuple(
                    nearest_integer((previous - raw_value) / direction_quantum)
                    for previous, raw_value, direction_quantum in zip(
                        previous_folded_directives,
                        directive_polarizations,
                        directive_quanta,
                    )
                )
                folded_directives = tuple(
                    raw_value + shift * direction_quantum
                    for raw_value, shift, direction_quantum in zip(
                        directive_polarizations,
                        branch_shifts,
                        directive_quanta,
                    )
                )
            (
                reduced_polarizations,
                conventional_quanta,
                conventional_components,
                folded_cartesian,
            ) = conventional_representation(
                folded_directives, directive_quanta, cell
            )
            previous_folded_directives = folded_directives
            folded_directive_rows.append(
                (
                    functional_dir.name,
                    geometry,
                    folded_directives,
                    conventional_components,
                    conventional_quanta,
                    folded_cartesian,
                )
            )
            rows.append({
                "functional": functional_dir.name,
                "geometry": geometry,
                "raw_polarization_x_C_per_m2": f"{raw_cartesian[0]:.12f}",
                "raw_polarization_y_C_per_m2": f"{raw_cartesian[1]:.12f}",
                "raw_polarization_z_C_per_m2": f"{raw_cartesian[2]:.12f}",
                "raw_polarization_1_C_per_m2": f"{directive_polarizations[0]:.12f}",
                "raw_polarization_2_C_per_m2": f"{directive_polarizations[1]:.12f}",
                "raw_polarization_3_C_per_m2": f"{directive_polarizations[2]:.12f}",
                "polarization_quantum_1_C_per_m2": f"{directive_quanta[0]:.9f}",
                "polarization_quantum_2_C_per_m2": f"{directive_quanta[1]:.9f}",
                "polarization_quantum_3_C_per_m2": f"{directive_quanta[2]:.9f}",
                "branch_shift_1_quanta": branch_shifts[0],
                "branch_shift_2_quanta": branch_shifts[1],
                "branch_shift_3_quanta": branch_shifts[2],
                "folded_polarization_1_C_per_m2": f"{folded_directives[0]:.12f}",
                "folded_polarization_2_C_per_m2": f"{folded_directives[1]:.12f}",
                "folded_polarization_3_C_per_m2": f"{folded_directives[2]:.12f}",
                "reduced_polarization_1": f"{reduced_polarizations[0]:.12f}",
                "reduced_polarization_2": f"{reduced_polarizations[1]:.12f}",
                "reduced_polarization_3": f"{reduced_polarizations[2]:.12f}",
                "conventional_quantum_1_C_per_m2": f"{conventional_quanta[0]:.12f}",
                "conventional_quantum_2_C_per_m2": f"{conventional_quanta[1]:.12f}",
                "conventional_quantum_3_C_per_m2": f"{conventional_quanta[2]:.12f}",
                "folded_conventional_polarization_1_C_per_m2": f"{conventional_components[0]:.12f}",
                "folded_conventional_polarization_2_C_per_m2": f"{conventional_components[1]:.12f}",
                "folded_conventional_polarization_3_C_per_m2": f"{conventional_components[2]:.12f}",
                "folded_polarization_x_C_per_m2": f"{folded_cartesian[0]:.12f}",
                "folded_polarization_y_C_per_m2": f"{folded_cartesian[1]:.12f}",
                "folded_polarization_z_C_per_m2": f"{folded_cartesian[2]:.12f}",
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
        print(
            f"{functional}: branch-unwrapped conventional P1, P2, P3 "
            "(signed magnitudes along a1, a2, a3; C/m^2):"
        )
        functional_directives = {}
        for (
            directive_functional,
            geometry,
            folded_directives,
            conventional_components,
            conventional_quanta,
            folded_cartesian,
        ) in folded_directive_rows:
            if directive_functional != functional:
                continue
            functional_directives[geometry] = (
                folded_directives,
                conventional_components,
                conventional_quanta,
                folded_cartesian,
            )
            print(
                f"  n={geometry}: P1={conventional_components[0]:.9f}  "
                f"P2={conventional_components[1]:.9f}  "
                f"P3={conventional_components[2]:.9f}"
            )

        if 0 in functional_directives and 9 in functional_directives:
            (
                initial_directives,
                initial_components,
                initial_conventional_quanta,
                initial_cartesian,
            ) = functional_directives[0]
            (
                final_directives,
                final_components,
                final_conventional_quanta,
                final_cartesian,
            ) = functional_directives[9]
            projected_difference = tuple(
                final - initial
                for initial, final in zip(initial_directives, final_directives)
            )
            conventional_difference = tuple(
                final - initial
                for initial, final in zip(initial_components, final_components)
            )
            cartesian_difference = tuple(
                final - initial
                for initial, final in zip(initial_cartesian, final_cartesian)
            )
            modulus = math.sqrt(sum(component ** 2 for component in cartesian_difference))
            print(
                f"{functional}: conventional P(n=9) - P(n=0) (C/m^2): "
                f"ΔP1={conventional_difference[0]:.9f}  "
                f"ΔP2={conventional_difference[1]:.9f}  "
                f"ΔP3={conventional_difference[2]:.9f}"
            )
            print(
                f"{functional}: conventional vector-quantum magnitudes (C/m^2): "
                f"n=0 ({initial_conventional_quanta[0]:.9f}, "
                f"{initial_conventional_quanta[1]:.9f}, "
                f"{initial_conventional_quanta[2]:.9f}); "
                f"n=9 ({final_conventional_quanta[0]:.9f}, "
                f"{final_conventional_quanta[1]:.9f}, "
                f"{final_conventional_quanta[2]:.9f})"
            )
            print(
                f"{functional}: Cartesian difference from endpoint-specific cells "
                f"(C/m^2): ΔPx={cartesian_difference[0]:.9f}  "
                f"ΔPy={cartesian_difference[1]:.9f}  "
                f"ΔPz={cartesian_difference[2]:.9f}"
            )
            print(f"{functional}: |ΔP| = {modulus:.9f} C/m^2")
            print(
                f"{functional}: FHI projected difference used for branch tracking "
                f"(C/m^2): Δp1={projected_difference[0]:.9f}  "
                f"Δp2={projected_difference[1]:.9f}  "
                f"Δp3={projected_difference[2]:.9f}"
            )
        else:
            print(f"{functional}: folded n=9 - n=0 difference is not available")

        quanta = ", ".join(
            f"n={row['geometry']}: ({float(row['polarization_quantum_1_C_per_m2']):.9f}, "
            f"{float(row['polarization_quantum_2_C_per_m2']):.9f}, "
            f"{float(row['polarization_quantum_3_C_per_m2']):.9f})"
            for row in functional_rows
        )
        print(f"{functional}: FHI projected P1/P2/P3 quanta (C/m^2): {quanta}")


if __name__ == "__main__":
    main()
