#!/usr/bin/env python3

"""Extract polarization wall times for the atom-scaling calculations."""

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

SUCCESS_MARKER = "Have a nice day."


def read_aims_output(outfile):
    """Return wall time and atom count from a completed FHI-aims output."""

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


def numbered_directories(base, prefix):
    """Return directories named ``prefix-N`` in numerical order."""

    directories = []
    for path in base.glob(f"{prefix}-*"):
        if not path.is_dir():
            continue
        try:
            number = int(path.name.removeprefix(f"{prefix}-"))
        except ValueError:
            print(f"[WARN] Ignoring unexpected directory {path.relative_to(base)}")
            continue
        directories.append((number, path))

    return sorted(directories)


def main():
    base = Path(__file__).resolve().parent
    rows = []

    for nodes, node_dir in numbered_directories(base, "nodes"):
        for supercell, supercell_dir in numbered_directories(node_dir, "supercell"):
            for method in ("lapack", "scalapack"):
                outputs = {
                    calculation: supercell_dir
                    / method
                    / calculation
                    / "aims.out"
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
                        print(f"[WARN] Skipping {outfile.relative_to(base)}: {error}")
                        failed = True

                if failed:
                    continue

                scf_time, scf_atoms = results["scf"]
                dipole_time, dipole_atoms = results["dipole"]
                if scf_atoms != dipole_atoms:
                    print(
                        f"[WARN] Skipping nodes-{nodes}/supercell-{supercell}/"
                        f"{method}: atom counts differ ({scf_atoms} and "
                        f"{dipole_atoms})"
                    )
                    continue

                if scf_atoms == 2:
                    continue

                # FHI-aims reports timings to milliseconds, so retain that
                # precision when subtracting the reference SCF run.
                polarization_time = round(dipole_time - scf_time, 3)
                if polarization_time <= 0:
                    print(
                        f"[WARN] Skipping nodes-{nodes}/supercell-{supercell}/"
                        f"{method}: non-positive polarization time "
                        f"({polarization_time:.3f} s)"
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
                    }
                )

                print(
                    f"{nodes} nodes | supercell {supercell:>2} | "
                    f"{method:10s} | {scf_atoms:>4} atoms | "
                    f"{polarization_time:.3f} s"
                )

    if not rows:
        raise RuntimeError("No complete SCF/dipole calculation pairs were found")

    rows.sort(key=lambda row: (row["nodes"], row["method"], row["atoms"]))
    output = base / "dataframe.csv"
    with output.open("w", newline="") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    print(f"\nSaved {output}")


if __name__ == "__main__":
    main()
