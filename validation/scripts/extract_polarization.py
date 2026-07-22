#!/usr/bin/env python3
"""Extract Cartesian polarizations and compare LAPACK/ScaLAPACK.

The expected directory layout is::

    <material>/<structure>/<functional>/{lapack,scalapack}/aims.out

Missing files (or outputs without a Cartesian-polarization line) are retained
in the CSV with a descriptive status rather than causing the script to fail.
"""

from __future__ import annotations

import argparse
import csv
import math
import re
from pathlib import Path
from typing import Optional


FUNCTIONALS = ("HSE06", "LDA", "PBEsol")
BACKENDS = ("lapack", "scalapack")
MARKER = "| Cartesian Polarization"
NUMBER_TEXT = r"[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[EeDd][+-]?\d+)?"
NUMBER = re.compile(NUMBER_TEXT)
FULL_DIRECTIVE = re.compile(
    rf"Directive\s+([123])\b.*?yields the full polarization\s*:\s*({NUMBER_TEXT})"
)


def read_polarization(path: Path) -> tuple[Optional[tuple[float, float, float]], str]:
    """Return the final Cartesian-polarization vector in ``path`` in C/m^2."""
    if not path.is_file():
        return None, "missing_aims.out"

    last_values: Optional[tuple[float, float, float]] = None
    try:
        with path.open(encoding="utf-8", errors="replace") as output:
            for line in output:
                if MARKER not in line:
                    continue
                values = NUMBER.findall(line.split(MARKER, 1)[1])
                if len(values) < 3:
                    continue
                last_values = tuple(float(value.replace("D", "E").replace("d", "e"))
                                    for value in values[:3])
    except OSError as error:
        return None, f"read_error: {error.strerror or error}"

    if last_values is None:
        return None, "polarization_not_found"
    return last_values, "ok"


def read_full_directive_polarizations(
    path: Path,
) -> tuple[Optional[tuple[float, float, float]], str]:
    """Return final full polarizations along periodic directions 1, 2, and 3."""
    if not path.is_file():
        return None, "missing_aims.out"

    values: list[Optional[float]] = [None, None, None]
    try:
        with path.open(encoding="utf-8", errors="replace") as output:
            for line in output:
                match = FULL_DIRECTIVE.search(line)
                if match:
                    direction = int(match.group(1)) - 1
                    values[direction] = float(match.group(2).replace("D", "E").replace("d", "e"))
    except OSError as error:
        return None, f"read_error: {error.strerror or error}"

    if any(value is None for value in values):
        return None, "full_directive_polarization_not_found"
    return tuple(values), "ok"  # type: ignore[arg-type]


def values_for_csv(values: Optional[tuple[float, float, float]]) -> list[str]:
    return ["" if value is None else f"{value:.15g}" for value in (values or (None,) * 3)]


def compare(
    lapack: Optional[tuple[float, float, float]],
    scalapack: Optional[tuple[float, float, float]],
    rtol: float,
    atol: float,
) -> tuple[str, Optional[float]]:
    if lapack is None or scalapack is None:
        return "not_compared_missing_value", None
    differences = [abs(left - right) for left, right in zip(lapack, scalapack)]
    matches = all(math.isclose(left, right, rel_tol=rtol, abs_tol=atol)
                  for left, right in zip(lapack, scalapack))
    return ("match" if matches else "mismatch"), max(differences)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "material_dir", nargs="?", type=Path, default=Path("validation/BaTiO3"),
        help="material directory (default: validation/BaTiO3)",
    )
    parser.add_argument(
        "--structures", nargs=2, metavar=("REFERENCE", "COMPARISON"),
        default=("cubic", "rhombohedral"),
        help=("two structure subfolders; the script prints COMPARISON minus "
              "REFERENCE (default: cubic rhombohedral)"),
    )
    parser.add_argument(
        "--output", "-o", type=Path,
        help="destination CSV (default: <material_dir>/cartesian_polarization.csv)",
    )
    parser.add_argument("--rtol", type=float, default=1e-8, help="relative comparison tolerance")
    parser.add_argument("--atol", type=float, default=1e-12, help="absolute comparison tolerance in C/m^2")
    args = parser.parse_args()

    if not args.material_dir.is_dir():
        parser.error(f"directory does not exist: {args.material_dir}")
    if args.structures[0] == args.structures[1]:
        parser.error("the two structure subfolders must be different")
    if args.output is None:
        args.output = args.material_dir / "cartesian_polarization.csv"

    structures = args.structures
    rows = []
    cartesian_polarizations = {}
    lapack_directives = {}
    for structure in structures:
        for functional in FUNCTIONALS:
            vectors = {}
            statuses = {}
            for backend in BACKENDS:
                path = args.material_dir / structure / functional / backend / "aims.out"
                vectors[backend], statuses[backend] = read_polarization(path)
                cartesian_polarizations[(structure, functional, backend)] = (
                    vectors[backend], statuses[backend]
                )
            lapack_path = args.material_dir / structure / functional / "lapack" / "aims.out"
            lapack_directives[(structure, functional)] = read_full_directive_polarizations(lapack_path)
            comparison, max_difference = compare(
                vectors["lapack"], vectors["scalapack"], args.rtol, args.atol
            )
            rows.append([
                structure, functional,
                *values_for_csv(vectors["lapack"]), statuses["lapack"],
                *values_for_csv(vectors["scalapack"]), statuses["scalapack"],
                "" if max_difference is None else f"{max_difference:.15g}", comparison,
            ])

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", newline="", encoding="utf-8") as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow([
            "structure", "functional",
            "lapack_px_C_m2", "lapack_py_C_m2", "lapack_pz_C_m2", "lapack_status",
            "scalapack_px_C_m2", "scalapack_py_C_m2", "scalapack_pz_C_m2", "scalapack_status",
            "max_abs_difference_C_m2", "comparison",
        ])
        writer.writerows(rows)

    print(f"Wrote {len(rows)} rows to {args.output}")
    for row in rows:
        print(f"{row[0]:12} {row[1]:7} {row[-1]}")

    print("\nLAPACK full polarization along periodic directions (C/m^2):")
    for (structure, functional), (values, status) in lapack_directives.items():
        if values is None:
            print(f"{structure:12} {functional:7} {status}")
        else:
            print(
                f"{structure:12} {functional:7} "
                f"P1={values[0]:.9g}  P2={values[1]:.9g}  P3={values[2]:.9g}"
            )

    reference, comparison_structure = structures
    print(
        f"\n{comparison_structure} minus {reference} "
        "LAPACK full polarization (C/m^2):"
    )
    for functional in FUNCTIONALS:
        reference_values, reference_status = lapack_directives.get(
            (reference, functional), (None, "missing")
        )
        comparison_values, comparison_status = lapack_directives.get(
            (comparison_structure, functional), (None, "missing")
        )
        if reference_values is None or comparison_values is None:
            print(f"{functional:7} not available ({reference_status}; {comparison_status})")
            continue
        difference = tuple(
            right - left for left, right in zip(reference_values, comparison_values)
        )
        print(
            f"{functional:7} "
            f"ΔP1={difference[0]:.9g}  ΔP2={difference[1]:.9g}  ΔP3={difference[2]:.9g}"
        )

    print(
        f"\n{comparison_structure} minus {reference} "
        "Cartesian polarization (C/m^2):"
    )
    for functional in FUNCTIONALS:
        for backend in BACKENDS:
            reference_values, reference_status = cartesian_polarizations[
                (reference, functional, backend)
            ]
            comparison_values, comparison_status = cartesian_polarizations[
                (comparison_structure, functional, backend)
            ]
            if reference_values is None or comparison_values is None:
                print(
                    f"{functional:7} {backend:9} not available "
                    f"({reference_status}; {comparison_status})"
                )
                continue
            difference = tuple(
                right - left for left, right in zip(reference_values, comparison_values)
            )
            modulus = math.sqrt(sum(component ** 2 for component in difference))
            print(
                f"{functional:7} {backend:9} "
                f"ΔPx={difference[0]:.9g}  ΔPy={difference[1]:.9g}  "
                f"ΔPz={difference[2]:.9g}  |ΔP|={modulus:.9g}"
            )

    comparisons = [row[-1] for row in rows]
    if "mismatch" in comparisons:
        print("Mismatch found: LAPACK and ScaLAPACK do not agree for every complete pair.")
        return 1
    if "match" in comparisons:
        print("Everything is okay: LAPACK and ScaLAPACK return the same values.")
    else:
        print("No complete LAPACK/ScaLAPACK pairs were available to compare.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
