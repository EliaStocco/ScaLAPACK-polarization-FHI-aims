#!/usr/bin/env python3
"""Collect the relaxed validation geometries for the fd2bec analysis.

For every ``validation/<system>/<phase>/<xc>/lapack/geometry.in`` the A-site
atom (Ba, Pb or Bi) is moved to the top of the atom list, so that fd2bec's
``tensor_symmetries`` places it at the origin, as in Table S5.  Each reordered
geometry is written to ``geometries/<system>_<phase>_<xc>.in`` and all of them
are collected in ``geometries/all.extxyz`` for ``space_group_dataset``.
"""

from pathlib import Path

from ase.io import read, write

HERE = Path(__file__).resolve().parent
VALIDATION = HERE.parent
SYSTEMS = ("BaTiO3", "PbTiO3", "BiFeO3")
A_SITES = ("Ba", "Pb", "Bi")


def main() -> None:
    output = HERE / "geometries"
    output.mkdir(exist_ok=True)
    frames, names = [], []
    for system in SYSTEMS:
        for path in sorted((VALIDATION / system).glob("*/*/lapack/geometry.in")):
            phase, xc = path.parts[-4], path.parts[-3]
            if xc.startswith("~"):  # exploratory runs, not used in the tables
                continue
            atoms = read(path, format="aims")
            symbols = atoms.get_chemical_symbols()
            a_site = next(s for s in A_SITES if s in symbols)
            order = [i for i, s in enumerate(symbols) if s == a_site]
            order += [i for i, s in enumerate(symbols) if s != a_site]
            atoms = atoms[order]
            name = f"{system}_{phase}_{xc}"
            write(output / f"{name}.in", atoms, format="aims")
            atoms.info["name"] = name
            frames.append(atoms)
            names.append(name)
    write(output / "all.extxyz", frames, format="extxyz")
    (output / "names.txt").write_text("\n".join(names) + "\n")
    print(f"Wrote {len(frames)} geometries to {output}")


if __name__ == "__main__":
    main()
