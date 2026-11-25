#!/usr/bin/env python3
"""Extract the old LAPACK and 2026-11-04 ScaLAPACK timings.

The old LAPACK ``aims.out`` files are stored below ``lapack/``.  The rerun
ScaLAPACK outputs are read directly from the accompanying ZIP archive, so no
external calculation directory is needed to reproduce ``dataframe.csv``.
"""

from __future__ import annotations

import argparse
import csv
import re
import zipfile
from pathlib import Path


BASE = Path(__file__).resolve().parent
LAPACK_DIRECTORY = BASE / "lapack"
SCALAPACK_ARCHIVE = BASE / "scalapack-rerun-20261104-outputs.zip"
SUCCESS_MARKER = "Have a nice day."
TOTAL_TIME_RE = re.compile(
    r"^\s*\|\s*Total time\s*:\s*"
    r"(?P<cpu>[\d.eE+-]+)\s*s\s+(?P<wall>[\d.eE+-]+)\s*s\s*$",
    re.MULTILINE,
)
ATOMS_RE = re.compile(
    r"^\s*\|\s*Number of atoms\s*:\s*(?P<atoms>\d+)\s*$",
    re.MULTILINE,
)
SCF_CYCLES_RE = re.compile(
    r"^\s*\|\s*Number of self-consistency cycles\s*:\s*"
    r"(?P<cycles>\d+)\s*$",
    re.MULTILINE,
)
LAPACK_PATH_RE = re.compile(r"(?P<cell>\d+x\d+x\d+)/lapack/(?P<run>scf|dipole)/aims\.out$")
SCALAPACK_PATH_RE = re.compile(
    r"supercell-(?P<cell>\d+x\d+x\d+)/scalapack/(?P<run>scf|dipole)/"
    r"rerun-20261104/aims\.rerun-20261104\.n=512\.out$"
)


def read_aims_output(text: str, description: str) -> tuple[float, int]:
    """Return final wall time and atom count from a completed one-cycle run."""

    if SUCCESS_MARKER not in text:
        raise ValueError(f"{description}: calculation did not finish successfully")
    timing = TOTAL_TIME_RE.search(text)
    atoms = ATOMS_RE.search(text)
    cycles = SCF_CYCLES_RE.search(text)
    if timing is None or atoms is None or cycles is None:
        raise ValueError(f"{description}: missing timing, atom count, or SCF-cycle count")
    if int(cycles.group("cycles")) != 1:
        raise ValueError(f"{description}: expected one SCF cycle")
    return float(timing.group("wall")), int(atoms.group("atoms"))


def collect_lapack() -> dict[str, dict[str, tuple[float, int]]]:
    """Read the preserved LAPACK SCF/dipole output pairs."""

    pairs: dict[str, dict[str, tuple[float, int]]] = {}
    for path in sorted(LAPACK_DIRECTORY.glob("*/lapack/*/aims.out")):
        relative = path.relative_to(LAPACK_DIRECTORY).as_posix()
        match = LAPACK_PATH_RE.fullmatch(relative)
        if match is None:
            continue
        cell, run = match.group("cell", "run")
        pairs.setdefault(cell, {})[run] = read_aims_output(
            path.read_text(errors="ignore"), str(path.relative_to(BASE))
        )
    return pairs


def collect_scalapack() -> dict[str, dict[str, tuple[float, int]]]:
    """Read the updated 512-rank ScaLAPACK SCF/dipole output pairs."""

    pairs: dict[str, dict[str, tuple[float, int]]] = {}
    with zipfile.ZipFile(SCALAPACK_ARCHIVE) as archive:
        for member in archive.namelist():
            match = SCALAPACK_PATH_RE.fullmatch(member)
            if match is None:
                continue
            cell, run = match.group("cell", "run")
            text = archive.read(member).decode(errors="ignore")
            pairs.setdefault(cell, {})[run] = read_aims_output(text, member)
    return pairs


def rows_for(method: str, pairs: dict[str, dict[str, tuple[float, int]]]) -> list[dict[str, object]]:
    """Turn complete output pairs into timing-table rows."""

    rows = []
    for cell, runs in pairs.items():
        if set(runs) != {"scf", "dipole"}:
            raise ValueError(f"{method} {cell}: missing SCF or dipole output")
        scf_time, scf_atoms = runs["scf"]
        dipole_time, dipole_atoms = runs["dipole"]
        if scf_atoms != dipole_atoms:
            print(f"[WARN] Skipping {method} {cell}: SCF and dipole atom counts differ")
            continue
        polarization_time = dipole_time - scf_time
        if polarization_time <= 0:
            # The 1x1x1 LAPACK pair predates the usable scaling series and has
            # a negative dipole-minus-SCF value.  It is kept as raw source data
            # but cannot represent a positive polarization timing.
            print(f"[WARN] Skipping {method} {cell}: non-positive polarization time")
            continue
        rows.append(
            {
                "supercell": cell,
                "atoms": scf_atoms,
                "method": method,
                "scf_time": scf_time,
                "dipole_time": dipole_time,
                "polarization_time": polarization_time,
            }
        )
    return rows


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output", type=Path, default=BASE / "dataframe.csv", help="CSV destination"
    )
    args = parser.parse_args()

    rows = rows_for("lapack", collect_lapack()) + rows_for(
        "scalapack", collect_scalapack()
    )
    rows.sort(key=lambda row: (int(row["atoms"]), str(row["method"])))
    with args.output.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=rows[0].keys(), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    print(f"Saved {args.output}")


if __name__ == "__main__":
    main()
