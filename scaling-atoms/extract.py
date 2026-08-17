#!/usr/bin/env python3

"""Extract polarization and SCF-convergence wall times for atom scaling."""

import csv
import re
from pathlib import Path


TIMING_REGEX = re.compile(
    r"^\s*\|\s*Total time\s*:\s*"
    r"(?P<cpu>[\d.eE+-]+)\s*s\s+"
    r"(?P<wall>[\d.eE+-]+)\s*s\s*$",
    re.MULTILINE,
)

NUMBER_OF_ATOMS_REGEX = re.compile(
    r"^\s*\|\s*Number of atoms\s*:\s*(?P<atoms>\d+)\s*$",
    re.MULTILINE,
)

SCF_CYCLES_REGEX = re.compile(
    r"^\s*\|\s*Number of self-consistency cycles\s*:\s*"
    r"(?P<cycles>\d+)\s*$",
    re.MULTILINE,
)

WANNIER_TIME_REGEX = re.compile(
    r"^\s*\|\s*Total time for Wannier Center Evolution\s*:\s*"
    r"(?P<cpu>[\d.eE+-]+)\s*s\s+"
    r"(?P<wall>[\d.eE+-]+)\s*s\s*$",
    re.MULTILINE,
)

FOURIER_EV_TIME_REGEX = re.compile(
    r"^\s*\|\s*Total Time for Fourier interpolated EV solution\s*:\s*"
    r"(?P<cpu>[\d.eE+-]+)\s+"
    r"(?P<wall>[\d.eE+-]+)\s*$",
    re.MULTILINE,
)

DIPOLE_MATRIX_TIME_REGEX = re.compile(
    r"^\s*\|\s*Total Time for dipole matrix\s*:\s*"
    r"(?P<cpu>[\d.eE+-]+)\s+"
    r"(?P<wall>[\d.eE+-]+)\s*$",
    re.MULTILINE,
)

DIPOLE_TERM_TIME_REGEX = re.compile(
    r"^\s*\|\s*Total Time for dipole term\s*:\s*"
    r"(?P<cpu>[\d.eE+-]+)\s+"
    r"(?P<wall>[\d.eE+-]+)\s*$",
    re.MULTILINE,
)

BERRY_TERM_TIME_REGEX = re.compile(
    r"^\s*\|\s*Total Time for berry term\s*:\s*"
    r"(?P<cpu>[\d.eE+-]+)\s+"
    r"(?P<wall>[\d.eE+-]+)\s*$",
    re.MULTILINE,
)

SUCCESS_MARKER = "Have a nice day."


def read_aims_output(outfile):
    """Return wall time and atom count from a single-cycle calculation."""

    text = outfile.read_text(errors="ignore")

    if SUCCESS_MARKER not in text:
        raise ValueError("calculation did not finish successfully")

    timing = TIMING_REGEX.search(text)
    if timing is None:
        raise ValueError("could not find total timing")

    atoms = NUMBER_OF_ATOMS_REGEX.search(text)
    if atoms is None:
        raise ValueError("could not find number of atoms")

    cycles = SCF_CYCLES_REGEX.search(text)
    if cycles is None:
        raise ValueError("could not find number of SCF cycles")

    if int(cycles.group("cycles")) != 1:
        raise ValueError(
            f"expected one SCF cycle, found {cycles.group('cycles')}"
        )

    return float(timing.group("wall")), int(atoms.group("atoms"))


def read_convergence_output(outfile):
    """Return total wall time and atom count from a converged SCF calculation."""

    text = outfile.read_text(errors="ignore")

    if SUCCESS_MARKER not in text:
        raise ValueError("calculation did not finish successfully")

    timing = TIMING_REGEX.search(text)
    if timing is None:
        raise ValueError("could not find total timing")

    atoms = NUMBER_OF_ATOMS_REGEX.search(text)
    if atoms is None:
        raise ValueError("could not find number of atoms")

    return (
        float(timing.group("wall")),
        int(atoms.group("atoms")),
    )


def read_component_time(text, regex, name):
    """Return the second timing value for one timing component."""

    timing = regex.search(text)

    if timing is None:
        raise ValueError(f"could not find {name} timing")

    return float(timing.group("wall"))


def numbered_directories(base, prefix):
    """Return directories named ``prefix-N`` in numerical order."""

    directories = []

    for path in base.glob(f"{prefix}-*"):
        if not path.is_dir():
            continue

        try:
            number = int(path.name.removeprefix(f"{prefix}-"))
        except ValueError:
            print(
                f"[WARN] Ignoring unexpected directory "
                f"{path.relative_to(base)}"
            )
            continue

        directories.append((number, path))

    return sorted(directories)


def main():
    base = Path(__file__).resolve().parent
    rows = []

    node_directories = (
        (2, base / "nodes-2-light"),
        (4, base / "nodes-4-light"),
    )

    for nodes, node_dir in node_directories:
        for supercell, supercell_dir in numbered_directories(
            node_dir,
            "supercell",
        ):

            # ---------------------------------------------------------
            # SCF convergence timing
            #
            # These calculations currently exist only for nodes-2-light:
            #
            # nodes-2-light/supercell-*/converge/aims.out
            # ---------------------------------------------------------
            converge_time = None
            converge_atoms = None

            if nodes == 2:
                converge_output = (
                    supercell_dir
                    / "converge"
                    / "aims.out"
                )

                if not converge_output.exists():
                    print(
                        f"[WARN] Missing "
                        f"{converge_output.relative_to(base)}"
                    )
                else:
                    try:
                        converge_time, converge_atoms = (
                            read_convergence_output(converge_output)
                        )
                    except ValueError as error:
                        print(
                            f"[WARN] Could not read "
                            f"{converge_output.relative_to(base)}: "
                            f"{error}"
                        )
                        converge_time = None
                        converge_atoms = None

            # ---------------------------------------------------------
            # Polarization calculations
            # ---------------------------------------------------------
            for method in ("lapack", "scalapack"):

                outputs = {
                    calculation: (
                        supercell_dir
                        / method
                        / calculation
                        / "aims.out"
                    )
                    for calculation in ("scf", "dipole")
                }

                missing = [
                    path.relative_to(base)
                    for path in outputs.values()
                    if not path.exists()
                ]

                if missing:
                    for path in missing:
                        print(f"[WARN] Missing {path}")
                    continue

                results = {}
                failed = False

                for calculation, outfile in outputs.items():
                    try:
                        results[calculation] = read_aims_output(outfile)
                    except ValueError as error:
                        print(
                            f"[WARN] Skipping "
                            f"{outfile.relative_to(base)}: {error}"
                        )
                        failed = True

                if failed:
                    continue

                scf_time, scf_atoms = results["scf"]
                dipole_time, dipole_atoms = results["dipole"]

                if scf_atoms != dipole_atoms:
                    print(
                        f"[WARN] Skipping nodes-{nodes}/"
                        f"supercell-{supercell}/{method}: "
                        f"atom counts differ "
                        f"({scf_atoms} and {dipole_atoms})"
                    )
                    continue

                if (
                    converge_atoms is not None
                    and converge_atoms != scf_atoms
                ):
                    print(
                        f"[WARN] nodes-{nodes}/"
                        f"supercell-{supercell}: "
                        f"convergence atom count differs "
                        f"({converge_atoms} vs {scf_atoms})"
                    )
                    continue

                if scf_atoms == 2:
                    continue

                # FHI-aims reports timings to milliseconds.
                polarization_time = round(
                    dipole_time - scf_time,
                    3,
                )

                if polarization_time <= 0:
                    print(
                        f"[WARN] Skipping nodes-{nodes}/"
                        f"supercell-{supercell}/{method}: "
                        f"non-positive polarization time "
                        f"({polarization_time:.3f} s)"
                    )
                    continue

                # Detailed component timings are extracted only
                # from ScaLAPACK dipole calculations.
                wannier_time = None
                fourier_ev_time = None
                dipole_matrix_time = None
                dipole_term_time = None
                berry_term_time = None

                if method == "scalapack":
                    dipole_text = outputs["dipole"].read_text(
                        errors="ignore"
                    )

                    try:
                        wannier_time = read_component_time(
                            dipole_text,
                            WANNIER_TIME_REGEX,
                            "Wannier Center Evolution",
                        )

                        fourier_ev_time = read_component_time(
                            dipole_text,
                            FOURIER_EV_TIME_REGEX,
                            "Fourier interpolated EV solution",
                        )

                        dipole_matrix_time = read_component_time(
                            dipole_text,
                            DIPOLE_MATRIX_TIME_REGEX,
                            "dipole matrix",
                        )

                        dipole_term_time = read_component_time(
                            dipole_text,
                            DIPOLE_TERM_TIME_REGEX,
                            "dipole term",
                        )

                        berry_term_time = read_component_time(
                            dipole_text,
                            BERRY_TERM_TIME_REGEX,
                            "berry term",
                        )

                    except ValueError as error:
                        print(
                            f"[WARN] Skipping "
                            f"{outputs['dipole'].relative_to(base)}: "
                            f"{error}"
                        )
                        continue

                rows.append(
                    {
                        "nodes": nodes,
                        "supercell": supercell,
                        "atoms": scf_atoms,
                        "method": method,
                        "scf_time": scf_time,
                        "dipole_time": dipole_time,
                        "polarization_time": polarization_time,
                        "converge_time": converge_time,
                        "wannier_time": wannier_time,
                        "fourier_ev_time": fourier_ev_time,
                        "dipole_matrix_time": dipole_matrix_time,
                        "dipole_term_time": dipole_term_time,
                        "berry_term_time": berry_term_time,
                    }
                )

                message = (
                    f"{nodes} nodes | "
                    f"supercell {supercell:>2} | "
                    f"{method:10s} | "
                    f"{scf_atoms:>4} atoms | "
                    f"polarization {polarization_time:.3f} s"
                )

                if converge_time is not None:
                    message += (
                        f" | converge {converge_time:.3f} s"
                    )

                if method == "scalapack":
                    message += (
                        f" | WCE {wannier_time:.3f} s"
                        f" | Fourier EV {fourier_ev_time:.3f} s"
                        f" | dipole matrix "
                        f"{dipole_matrix_time:.3f} s"
                        f" | dipole term {dipole_term_time:.3f} s"
                        f" | berry term {berry_term_time:.3f} s"
                    )

                print(message)

    if not rows:
        raise RuntimeError(
            "No complete SCF/dipole calculation pairs were found"
        )

    rows.sort(
        key=lambda row: (
            row["nodes"],
            row["method"],
            row["atoms"],
        )
    )

    output = base / "dataframe.csv"

    fieldnames = [
        "nodes",
        "supercell",
        "atoms",
        "method",
        "scf_time",
        "dipole_time",
        "polarization_time",
        "converge_time",
        "wannier_time",
        "fourier_ev_time",
        "dipole_matrix_time",
        "dipole_term_time",
        "berry_term_time",
    ]

    with output.open("w", newline="") as csvfile:
        writer = csv.DictWriter(
            csvfile,
            fieldnames=fieldnames,
        )
        writer.writeheader()
        writer.writerows(rows)

    print(f"\nSaved {output}")


if __name__ == "__main__":
    main()