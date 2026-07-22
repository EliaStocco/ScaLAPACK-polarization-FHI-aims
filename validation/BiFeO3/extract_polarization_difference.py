#!/usr/bin/env python3
"""Extract the R-3c-to-R3c BiFeO3 polarization difference.

By default, symmetry-equivalent R-3c components are first put on the same
branch.  The R3c image is then placed on the positive, continuous branch of the
R-3c-to-R3c distortion used in ``validation/test-BiFeO3``.  Alternative branch
choices can be supplied explicitly or selected with ``--nearest-branch``.
"""

from __future__ import annotations

import argparse
import csv
import itertools
import math
import re
import sys
from dataclasses import dataclass
from pathlib import Path


ELEMENTARY_CHARGE_C = 1.602176634e-19
ANGSTROM2_TO_M2 = 1.0e-20
REFERENCE_PHASE = "BiFeO3_R-3c_AFM"
POLAR_PHASE = "BiFeO3_R3c_AFM"
FULL_POLARIZATION_RE = re.compile(
    r"Directive\s+([123])\b.*?yields the full polarization\s*:\s*"
    r"([-+]?\d*\.?\d+(?:[Ee][-+]?\d+)?)"
)
Vector = tuple[float, float, float]
Cell = tuple[Vector, Vector, Vector]


@dataclass(frozen=True)
class Snapshot:
    path: Path
    printed_cartesian: Vector
    projected_polarization: Vector
    projected_quanta: Vector
    cell: Cell


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


def subtract(left: Vector, right: Vector) -> Vector:
    return tuple(a - b for a, b in zip(left, right))


def projected_quantum_magnitudes(cell: Cell) -> Vector:
    """Return the FHI-aims projected quanta e/|a_j x a_k| in C/m^2."""
    face_areas = (
        norm(cross(cell[1], cell[2])),
        norm(cross(cell[2], cell[0])),
        norm(cross(cell[0], cell[1])),
    )
    return tuple(
        ELEMENTARY_CHARGE_C / ANGSTROM2_TO_M2 / area
        for area in face_areas
    )


def parse_output(path: Path) -> Snapshot:
    """Read the final polarization block and full-precision cell from aims.out."""
    printed_cartesian = None
    projected = [None, None, None]
    lattice_vectors = []

    for line in path.read_text(errors="replace").splitlines():
        fields = line.split()
        if fields and fields[0].lower() == "lattice_vector" and len(fields) >= 4:
            lattice_vectors.append(tuple(float(value) for value in fields[1:4]))
        match = FULL_POLARIZATION_RE.search(line)
        if match:
            projected[int(match.group(1)) - 1] = float(match.group(2))
        if "Cartesian Polarization" in line:
            printed_cartesian = tuple(float(value) for value in fields[-3:])

    if printed_cartesian is None or any(value is None for value in projected):
        raise ValueError(f"No complete final polarization block in {path}")
    if len(lattice_vectors) < 3:
        raise ValueError(f"No complete direct lattice in {path}")

    cell = tuple(lattice_vectors[-3:])
    return Snapshot(
        path=path,
        printed_cartesian=printed_cartesian,
        projected_polarization=tuple(projected),
        projected_quanta=projected_quantum_magnitudes(cell),
        cell=cell,
    )


def conventional_representation(
    projected_polarization: Vector,
    projected_quanta: Vector,
    cell: Cell,
) -> tuple[Vector, Vector, Vector, Vector]:
    """Return reduced P, conventional quanta/components, and Cartesian P."""
    volume = abs(dot(cell[0], cross(cell[1], cell[2])))
    if math.isclose(volume, 0.0, abs_tol=1e-15):
        raise ValueError("Cell has zero volume")

    factor = ELEMENTARY_CHARGE_C / ANGSTROM2_TO_M2 / volume
    quantum_vectors = tuple(
        tuple(factor * component for component in lattice_vector)
        for lattice_vector in cell
    )
    conventional_quanta = tuple(norm(vector) for vector in quantum_vectors)
    reduced = tuple(
        polarization / quantum
        for polarization, quantum in zip(projected_polarization, projected_quanta)
    )
    conventional_components = tuple(
        value * quantum for value, quantum in zip(reduced, conventional_quanta)
    )
    cartesian = tuple(
        sum(
            reduced[direction] * quantum_vectors[direction][component]
            for direction in range(3)
        )
        for component in range(3)
    )
    return reduced, conventional_quanta, conventional_components, cartesian


def usable_output(path: Path) -> bool:
    if not path.is_file():
        return False
    text = path.read_text(errors="replace")
    return "Cartesian Polarization" in text and all(
        f"Directive    {direction}" in text for direction in (1, 2, 3)
    )


def find_output(
    results_root: Path,
    phase: str,
    functional: str,
    method: str,
) -> Path:
    base = results_root / phase / functional
    if method != "auto":
        candidates = [base / method / "aims.out"]
    else:
        candidates = [
            base / name / "aims.out"
            for name in ("scalapack", "lapack", "converge")
        ]
        candidates.extend((base / "results" / "aims.out", base / "aims.out"))
    for candidate in candidates:
        if usable_output(candidate):
            return candidate
    raise FileNotFoundError(
        f"No complete polarization output found for {phase}/{functional}"
    )


def symmetry_aligned_shifts(snapshot: Snapshot) -> tuple[int, int, int]:
    """Put symmetry-equivalent projected components near the first component."""
    reference = snapshot.projected_polarization[0]
    return tuple(
        round((reference - value) / quantum)
        for value, quantum in zip(
            snapshot.projected_polarization, snapshot.projected_quanta
        )
    )


def apply_branch_shifts(snapshot: Snapshot, shifts: tuple[int, int, int]) -> Vector:
    return tuple(
        value + shift * quantum
        for value, shift, quantum in zip(
            snapshot.projected_polarization, shifts, snapshot.projected_quanta
        )
    )


def positive_branch_shifts(
    initial_projected: Vector,
    final: Snapshot,
) -> tuple[int, int, int]:
    """Choose the first final image above the reference along each direction."""
    return tuple(
        math.ceil((initial_value - final_value) / quantum)
        for initial_value, final_value, quantum in zip(
            initial_projected,
            final.projected_polarization,
            final.projected_quanta,
        )
    )


def nearest_branch_shifts(
    initial: Snapshot,
    initial_projected: Vector,
    final: Snapshot,
) -> tuple[int, int, int]:
    """Choose the nearby final-image branch with the smallest Cartesian |delta P|."""
    centers = tuple(
        round((initial_value - final_value) / quantum)
        for initial_value, final_value, quantum in zip(
            initial_projected,
            final.projected_polarization,
            final.projected_quanta,
        )
    )
    best_shifts = None
    best_modulus = math.inf
    _, _, _, initial_cartesian = conventional_representation(
        initial_projected, initial.projected_quanta, initial.cell
    )
    for shifts in itertools.product(
        *(range(center - 1, center + 2) for center in centers)
    ):
        folded = tuple(
            value + shift * quantum
            for value, shift, quantum in zip(
                final.projected_polarization, shifts, final.projected_quanta
            )
        )
        _, _, _, final_cartesian = conventional_representation(
            folded, final.projected_quanta, final.cell
        )
        modulus = norm(subtract(final_cartesian, initial_cartesian))
        if modulus < best_modulus:
            best_shifts = shifts
            best_modulus = modulus
    assert best_shifts is not None
    return best_shifts


def main() -> None:
    script_dir = Path(__file__).resolve().parent
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--results-root",
        type=Path,
        default=script_dir,
        help=f"BiFeO3 results directory (default: {script_dir}).",
    )
    parser.add_argument(
        "--method",
        choices=("auto", "scalapack", "lapack", "converge"),
        default="auto",
        help="Output subdirectory to use; auto prefers ScaLAPACK (default: auto).",
    )
    branch_group = parser.add_mutually_exclusive_group()
    branch_group.add_argument(
        "--branch-shifts",
        nargs=3,
        type=int,
        metavar=("N1", "N2", "N3"),
        help="Add N_i polar-state polarization quanta before taking the difference.",
    )
    branch_group.add_argument(
        "--nearest-branch",
        action="store_true",
        help="Select the nearby polar branch giving the smallest Cartesian |delta P|.",
    )
    parser.add_argument(
        "--reference-branch-shifts",
        nargs=3,
        type=int,
        metavar=("N1", "N2", "N3"),
        help=(
            "Reference-state shifts; by default its symmetry-equivalent "
            "components are aligned automatically."
        ),
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=script_dir / "polarization_difference.csv",
        help="CSV output path (default: beside this script).",
    )
    args = parser.parse_args()

    phase_dirs = (
        args.results_root / REFERENCE_PHASE,
        args.results_root / POLAR_PHASE,
    )
    missing_phases = [str(path) for path in phase_dirs if not path.is_dir()]
    if missing_phases:
        raise SystemExit(f"Missing phase directory: {', '.join(missing_phases)}")

    functional_names = set.intersection(*(
        {path.name for path in phase_dir.iterdir() if path.is_dir()}
        for phase_dir in phase_dirs
    ))
    known_order = ("LDA", "PBEsol", "HSE06")
    functionals = [name for name in known_order if name in functional_names]
    functionals.extend(sorted(functional_names.difference(functionals)))

    rows = []
    for functional in functionals:
        try:
            initial = parse_output(find_output(
                args.results_root, REFERENCE_PHASE, functional, args.method
            ))
            final = parse_output(find_output(
                args.results_root, POLAR_PHASE, functional, args.method
            ))
        except (FileNotFoundError, ValueError) as error:
            print(f"WARNING: skipping {functional}: {error}", file=sys.stderr)
            continue

        if args.reference_branch_shifts is not None:
            initial_shifts = tuple(args.reference_branch_shifts)
            reference_branch_source = "explicit"
        else:
            initial_shifts = symmetry_aligned_shifts(initial)
            reference_branch_source = "symmetry aligned"
        shifted_initial = apply_branch_shifts(initial, initial_shifts)

        if args.branch_shifts is not None:
            final_shifts = tuple(args.branch_shifts)
            final_branch_source = "explicit"
        elif args.nearest_branch:
            final_shifts = nearest_branch_shifts(initial, shifted_initial, final)
            final_branch_source = "nearest Cartesian image"
        else:
            final_shifts = positive_branch_shifts(shifted_initial, final)
            final_branch_source = "positive continuous path"

        shifted_final = apply_branch_shifts(final, final_shifts)
        _, initial_quanta, initial_components, initial_cartesian = (
            conventional_representation(
                shifted_initial,
                initial.projected_quanta,
                initial.cell,
            )
        )
        _, final_quanta, final_components, final_cartesian = (
            conventional_representation(
                shifted_final, final.projected_quanta, final.cell
            )
        )
        conventional_delta = subtract(final_components, initial_components)
        cartesian_delta = subtract(final_cartesian, initial_cartesian)
        modulus = norm(cartesian_delta)

        print(
            f"{functional}: R-3c -> R3c; reference branch shifts "
            f"{initial_shifts} ({reference_branch_source}); polar branch shifts "
            f"{final_shifts} ({final_branch_source})"
        )
        print(
            "  conventional difference (C/m^2): "
            f"Delta P1={conventional_delta[0]:.9f}  "
            f"Delta P2={conventional_delta[1]:.9f}  "
            f"Delta P3={conventional_delta[2]:.9f}"
        )
        print(
            "  Cartesian difference (C/m^2): "
            f"Delta Px={cartesian_delta[0]:.9f}  "
            f"Delta Py={cartesian_delta[1]:.9f}  "
            f"Delta Pz={cartesian_delta[2]:.9f}"
        )
        print(f"  |Delta P| = {modulus:.9f} C/m^2")
        print(f"  inputs: {initial.path} ; {final.path}")

        rows.append({
            "functional": functional,
            "reference_branch_shift_1": initial_shifts[0],
            "reference_branch_shift_2": initial_shifts[1],
            "reference_branch_shift_3": initial_shifts[2],
            "polar_branch_shift_1": final_shifts[0],
            "polar_branch_shift_2": final_shifts[1],
            "polar_branch_shift_3": final_shifts[2],
            "delta_P1_conventional_C_per_m2": f"{conventional_delta[0]:.12f}",
            "delta_P2_conventional_C_per_m2": f"{conventional_delta[1]:.12f}",
            "delta_P3_conventional_C_per_m2": f"{conventional_delta[2]:.12f}",
            "delta_Px_C_per_m2": f"{cartesian_delta[0]:.12f}",
            "delta_Py_C_per_m2": f"{cartesian_delta[1]:.12f}",
            "delta_Pz_C_per_m2": f"{cartesian_delta[2]:.12f}",
            "modulus_delta_P_C_per_m2": f"{modulus:.12f}",
            "reference_Q1_conventional_C_per_m2": f"{initial_quanta[0]:.12f}",
            "reference_Q2_conventional_C_per_m2": f"{initial_quanta[1]:.12f}",
            "reference_Q3_conventional_C_per_m2": f"{initial_quanta[2]:.12f}",
            "polar_Q1_conventional_C_per_m2": f"{final_quanta[0]:.12f}",
            "polar_Q2_conventional_C_per_m2": f"{final_quanta[1]:.12f}",
            "polar_Q3_conventional_C_per_m2": f"{final_quanta[2]:.12f}",
            "reference_output": str(initial.path),
            "polar_output": str(final.path),
        })

    if not rows:
        raise SystemExit("No complete R-3c/R3c output pairs were found")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    print(f"Wrote {args.output}")


if __name__ == "__main__":
    main()
