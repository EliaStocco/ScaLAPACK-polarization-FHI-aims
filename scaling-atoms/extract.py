#!/usr/bin/env python3

"""Extract timings from the k-grid atom-scaling calculations.

The calculation folders are named ``supercell-AxBxC`` and contain the
convergence, LAPACK, and (where available) ScaLAPACK outputs directly.
"""

import argparse
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
BLACS_GRID_REGEX = re.compile(
    r"^\s*K-point:\s*\d+\s+Tasks:\s*(?P<tasks>\d+)\s+"
    r"split into\s*(?P<rows>\d+)\s+X\s+(?P<columns>\d+)\s+BLACS grid\s*$",
    re.MULTILINE,
)
SCALAPACK_BLOCK_SIZE_REGEX = re.compile(
    r"^\s*ScaLAPACK block size set to:\s*(?P<block_size>\d+)\s*$",
    re.MULTILINE,
)
POLARIZATION_REGEX = re.compile(
    r"^\s*output polarization\s+(?P<direction>[123])\s+"
    r"(?P<k1>\d+)\s+(?P<k2>\d+)\s+(?P<k3>\d+)\s*$",
    re.MULTILINE,
)
SCALAPACK_POLARIZATION_LISTING_REGEX = re.compile(
    r"^\s*Detailed listing of bands and assigned k-points in polarization "
    r"calculation:\s*\n"
    r"(?P<tasks>(?:\s*Task\s+\d+.*?-->\s+(?:useful|useless)\s*\n)+)",
    re.MULTILINE,
)
SCALAPACK_POLARIZATION_TASK_REGEX = re.compile(
    r"-->\s+(?P<status>useful|useless)\s*$",
    re.MULTILINE,
)
SUPERCELL_REGEX = re.compile(r"supercell-(\d+)x(\d+)x(\d+)$")
NODES_REGEX = re.compile(r"^\s*#SBATCH\s+--nodes=(\d+)\s*$", re.MULTILINE)
TASKS_PER_NODE_REGEX = re.compile(
    r"^\s*#SBATCH\s+--ntasks-per-node=(\d+)\s*$", re.MULTILINE
)
SUCCESS_MARKER = "Have a nice day."


def read_text(outfile):
    text = outfile.read_text(errors="ignore")
    if SUCCESS_MARKER not in text:
        raise ValueError("calculation did not finish successfully")
    return text


def read_aims_output(outfile, require_one_cycle=True):
    """Return wall time and number of atoms from a completed output."""
    text = read_text(outfile)
    timing = TIMING_REGEX.search(text)
    atoms = NUMBER_OF_ATOMS_REGEX.search(text)
    if timing is None:
        raise ValueError("could not find total timing")
    if atoms is None:
        raise ValueError("could not find number of atoms")

    if require_one_cycle:
        cycles = SCF_CYCLES_REGEX.search(text)
        if cycles is None:
            raise ValueError("could not find number of SCF cycles")
        if int(cycles.group("cycles")) != 1:
            raise ValueError(
                f"expected one SCF cycle, found {cycles.group('cycles')}"
            )

    return float(timing.group("wall")), int(atoms.group("atoms"))


def read_component_time(text, regex, name):
    timing = regex.search(text)
    if timing is None:
        raise ValueError(f"could not find {name} timing")
    return float(timing.group("wall"))


def read_blacs_configuration(text):
    """Return the BLACS task/grid dimensions and ScaLAPACK block size."""
    grid = BLACS_GRID_REGEX.search(text)
    block_size = SCALAPACK_BLOCK_SIZE_REGEX.search(text)
    if grid is None:
        raise ValueError("could not find BLACS grid")
    if block_size is None:
        raise ValueError("could not find ScaLAPACK block size")

    return {
        "blacs_tasks": int(grid.group("tasks")),
        "blacs_grid_rows": int(grid.group("rows")),
        "blacs_grid_columns": int(grid.group("columns")),
        "scalapack_block_size": int(block_size.group("block_size")),
    }


def read_lapack_polarization_cores(text):
    """Return the k-point count along the requested polarization direction."""
    polarization = POLARIZATION_REGEX.search(text)
    if polarization is None:
        raise ValueError("could not find output polarization setting")

    direction = int(polarization.group("direction"))
    k_points = [
        int(polarization.group("k1")),
        int(polarization.group("k2")),
        int(polarization.group("k3")),
    ]
    return k_points[direction - 1]


def read_scalapack_polarization_cores(text):
    """Return the common useful-task count from ScaLAPACK polarization listings."""
    useful_counts = []
    for listing in SCALAPACK_POLARIZATION_LISTING_REGEX.finditer(text):
        statuses = SCALAPACK_POLARIZATION_TASK_REGEX.findall(
            listing.group("tasks")
        )
        useful_counts.append(statuses.count("useful"))

    if not useful_counts:
        raise ValueError("could not find ScaLAPACK polarization task listings")
    if len(set(useful_counts)) != 1:
        raise ValueError(
            "ScaLAPACK polarization listings have different useful-task counts"
        )
    return useful_counts[0]


def supercell_directories(base):
    """Return ``supercell-AxBxC`` directories sorted by their volume."""
    directories = []
    for path in base.glob("supercell-*"):
        match = SUPERCELL_REGEX.fullmatch(path.name)
        if not path.is_dir() or match is None:
            continue
        dimensions = tuple(int(value) for value in match.groups())
        directories.append((dimensions, path))
    return sorted(directories, key=lambda item: (item[0][0] * item[0][1] * item[0][2], item[0]))


def read_nodes(job_script):
    """Read the Slurm node count, if the job script is available."""
    if not job_script.exists():
        return None
    match = NODES_REGEX.search(job_script.read_text(errors="ignore"))
    return int(match.group(1)) if match is not None else None


def read_allocated_cores(job_script):
    """Return the requested MPI rank count, if it is specified in the job script."""
    if not job_script.exists():
        return None
    script = job_script.read_text(errors="ignore")
    nodes = NODES_REGEX.search(script)
    tasks_per_node = TASKS_PER_NODE_REGEX.search(script)
    if nodes is None or tasks_per_node is None:
        return None
    return int(nodes.group(1)) * int(tasks_per_node.group(1))


def relative(path, base):
    return path.relative_to(base)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="CSV destination (default: dataframe.csv beside this script)",
    )
    args = parser.parse_args()

    base = Path(__file__).resolve().parent
    output = args.output or base / "dataframe.csv"
    rows = []

    for dimensions, supercell_dir in supercell_directories(base):
        supercell = "x".join(str(value) for value in dimensions)
        converge_output = supercell_dir / "converge" / "aims.out"
        converge_time = None
        converge_atoms = None

        if converge_output.exists():
            try:
                converge_time, converge_atoms = read_aims_output(
                    converge_output, require_one_cycle=False
                )
            except ValueError as error:
                print(f"[WARN] Could not read {relative(converge_output, base)}: {error}")
        elif converge_output.parent.exists():
            print(f"[WARN] Missing {relative(converge_output, base)}")

        for method in ("lapack", "scalapack"):
            method_dir = supercell_dir / method
            if not method_dir.is_dir():
                continue

            outputs = {
                calculation: method_dir / calculation / "aims.out"
                for calculation in ("scf", "dipole")
            }
            missing = [path for path in outputs.values() if not path.exists()]
            if missing:
                for path in missing:
                    print(f"[WARN] Missing {relative(path, base)}")
                continue

            try:
                scf_time, scf_atoms = read_aims_output(outputs["scf"])
                dipole_time, dipole_atoms = read_aims_output(outputs["dipole"])
            except ValueError as error:
                print(f"[WARN] Skipping {relative(supercell_dir / method, base)}: {error}")
                continue

            if scf_atoms != dipole_atoms:
                print(
                    f"[WARN] Skipping {supercell}/{method}: atom counts differ "
                    f"({scf_atoms} and {dipole_atoms})"
                )
                continue
            if converge_atoms is not None and converge_atoms != scf_atoms:
                print(
                    f"[WARN] Skipping {supercell}/{method}: convergence atom count "
                    f"differs ({converge_atoms} vs {scf_atoms})"
                )
                continue

            polarization_time = dipole_time - scf_time# round(dipole_time - scf_time, 3)
            if polarization_time <= 0:
                print(
                    f"[WARN] Skipping {supercell}/{method}: non-positive polarization "
                    f"time ({polarization_time:.3f} s)"
                )
                continue

            scf_job_script = supercell_dir / method / "scf" / "main.sh"
            dipole_job_script = supercell_dir / method / "dipole" / "main.sh"
            nodes = read_nodes(scf_job_script)
            dipole_nodes = read_nodes(dipole_job_script)
            if nodes is not None and dipole_nodes is not None and nodes != dipole_nodes:
                print(
                    f"[WARN] Skipping {supercell}/{method}: node counts differ "
                    f"({nodes} and {dipole_nodes})"
                )
                continue

            allocated_cores = read_allocated_cores(dipole_job_script)
            scf_allocated_cores = read_allocated_cores(scf_job_script)
            if (
                allocated_cores is not None
                and scf_allocated_cores is not None
                and allocated_cores != scf_allocated_cores
            ):
                print(
                    f"[WARN] Skipping {supercell}/{method}: requested MPI ranks differ "
                    f"({scf_allocated_cores} and {allocated_cores})"
                )
                continue

            try:
                if allocated_cores is None:
                    raise ValueError("could not find requested MPI rank count")
                dipole_text = read_text(outputs["dipole"])
                if method == "lapack":
                    polarization_cores = read_lapack_polarization_cores(dipole_text)
                else:
                    polarization_cores = read_scalapack_polarization_cores(dipole_text)
            except ValueError as error:
                print(f"[WARN] Skipping {relative(outputs['dipole'], base)}: {error}")
                continue

            polarization_cores_percentage = 100 * polarization_cores / allocated_cores

            component_times = {
                "wannier_time": None,
                "untracked_time": None,
                "fourier_ev_time": None,
                "dipole_matrix_time": None,
                "dipole_term_time": None,
                "berry_term_time": None,
            }
            blacs_configuration = {
                "blacs_tasks": None,
                "blacs_grid_rows": None,
                "blacs_grid_columns": None,
                "scalapack_block_size": None,
            }
            if method == "scalapack":
                scf_text = read_text(outputs["scf"])
                try:
                    wannier_time = read_component_time(
                        dipole_text,
                        WANNIER_TIME_REGEX,
                        "Wannier Center Evolution",
                    )
                    component_times = {
                        "wannier_time": wannier_time,
                        # Residual needed to reconcile the internal Wannier timer
                        # with the end-to-end dipole-minus-SCF measurement.  This
                        # includes unitemized initialization work, run-to-run
                        # variability, and smaller start/finalization differences;
                        # it is not a direct timer for save_overlap_scalapack.
                        "untracked_time": polarization_time - wannier_time,
                        "fourier_ev_time": read_component_time(dipole_text, FOURIER_EV_TIME_REGEX, "Fourier interpolated EV solution"),
                        "dipole_matrix_time": read_component_time(dipole_text, DIPOLE_MATRIX_TIME_REGEX, "dipole matrix"),
                        "dipole_term_time": read_component_time(dipole_text, DIPOLE_TERM_TIME_REGEX, "dipole term"),
                        "berry_term_time": read_component_time(dipole_text, BERRY_TERM_TIME_REGEX, "berry term"),
                    }
                    scf_blacs_configuration = read_blacs_configuration(scf_text)
                    blacs_configuration = read_blacs_configuration(dipole_text)
                except ValueError as error:
                    print(f"[WARN] Skipping {relative(outputs['dipole'], base)}: {error}")
                    continue

                if scf_blacs_configuration != blacs_configuration:
                    print(
                        f"[WARN] Skipping {supercell}/{method}: SCF and dipole "
                        "BLACS configurations differ"
                    )
                    continue

            row = {
                "nodes": nodes,
                "supercell": supercell,
                "atoms": scf_atoms,
                "method": method,
                "allocated_cores": allocated_cores,
                "polarization_cores": polarization_cores,
                "polarization_cores_percentage": polarization_cores_percentage,
                "scf_time": scf_time,
                "dipole_time": dipole_time,
                "polarization_time": polarization_time,
                "converge_time": converge_time,
                **component_times,
                **blacs_configuration,
            }
            rows.append(row)
            print(
                f"{nodes if nodes is not None else '?'} nodes | {supercell:>5} | "
                f"{method:10s} | {scf_atoms:>4} atoms | "
                f"polarization {polarization_time:.3f} s | "
                f"useful cores {polarization_cores_percentage:.2f}%"
            )

    if not rows:
        raise RuntimeError("No complete SCF/dipole calculation pairs were found")

    rows.sort(key=lambda row: (row["atoms"], row["method"]))
    fieldnames = [
        "nodes", "allocated_cores", "polarization_cores",
        "polarization_cores_percentage", "supercell", "atoms", "method",
        "scf_time", "dipole_time",
        "polarization_time", "converge_time", "wannier_time", "untracked_time",
        "fourier_ev_time", "dipole_matrix_time", "dipole_term_time", "berry_term_time",
        "blacs_tasks", "blacs_grid_rows", "blacs_grid_columns",
        "scalapack_block_size",
    ]
    with output.open("w", newline="") as csvfile:
        writer = csv.DictWriter(
            csvfile, fieldnames=fieldnames, lineterminator="\n"
        )
        writer.writeheader()
        writer.writerows(rows)
    print(f"\nSaved {output}")


if __name__ == "__main__":
    main()
