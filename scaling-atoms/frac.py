#!/usr/bin/env python3

import os
import shutil
import tempfile
import numpy as np

GEOMETRY_FILE = "geometry.in"
MAKE_BACKUP = True


def read_geometry(filename):
    """Read geometry.in and return its lines."""
    with open(filename, "r") as f:
        return f.readlines()


def get_lattice_vectors(lines):
    """Extract the three FHI-aims lattice vectors."""
    lattice = []

    for line in lines:
        stripped = line.strip()

        if not stripped or stripped.startswith("#"):
            continue

        parts = stripped.split()

        if parts[0].lower() == "lattice_vector":
            if len(parts) < 4:
                raise ValueError(f"Invalid lattice_vector line:\n{line}")

            lattice.append([
                float(parts[1]),
                float(parts[2]),
                float(parts[3])
            ])

    if len(lattice) != 3:
        raise ValueError(
            f"Expected exactly 3 lattice_vector lines, found {len(lattice)}."
        )

    return np.array(lattice, dtype=float)


def cartesian_to_fractional(cart, lattice):
    """
    Convert Cartesian coordinates to fractional coordinates.

    FHI-aims lattice vectors are stored as rows:
        r_cart = f1*a + f2*b + f3*c
    """
    return np.linalg.solve(lattice.T, cart)


def convert_geometry(lines, lattice):
    """Convert all 'atom' lines to 'atom_frac' lines."""
    new_lines = []

    for line in lines:
        stripped = line.strip()

        # Preserve blank lines and comments exactly
        if not stripped or stripped.startswith("#"):
            new_lines.append(line)
            continue

        parts = stripped.split()

        if parts[0].lower() == "atom":
            if len(parts) < 5:
                raise ValueError(f"Invalid atom line:\n{line}")

            cart = np.array([
                float(parts[1]),
                float(parts[2]),
                float(parts[3])
            ])

            frac = cartesian_to_fractional(cart, lattice)

            species = parts[4]

            # Preserve anything after the species, if present
            remainder = parts[5:]

            newline = (
                f"atom_frac "
                f"{frac[0]: .12f} "
                f"{frac[1]: .12f} "
                f"{frac[2]: .12f} "
                f"{species}"
            )

            if remainder:
                newline += " " + " ".join(remainder)

            newline += "\n"
            new_lines.append(newline)

        else:
            # lattice_vector, atom_frac, constraints, comments, etc.
            new_lines.append(line)

    return new_lines


def overwrite_file_safely(filename, lines):
    """Write to a temporary file, then replace the original."""
    directory = os.path.dirname(os.path.abspath(filename))

    fd, temp_name = tempfile.mkstemp(
        prefix=".geometry_tmp_",
        dir=directory,
        text=True
    )

    try:
        with os.fdopen(fd, "w") as f:
            f.writelines(lines)

        if MAKE_BACKUP:
            backup = filename + ".bak"
            shutil.copy2(filename, backup)
            print(f"Backup written to: {backup}")

        os.replace(temp_name, filename)

    except Exception:
        if os.path.exists(temp_name):
            os.remove(temp_name)
        raise


def main():
    lines = read_geometry(GEOMETRY_FILE)

    lattice = get_lattice_vectors(lines)

    print("Lattice vectors:")
    for vec in lattice:
        print(f"  {vec}")

    # Check that the cell is non-singular
    volume = abs(np.linalg.det(lattice))
    if volume < 1e-12:
        raise ValueError("The lattice vectors define a singular cell.")

    new_lines = convert_geometry(lines, lattice)

    overwrite_file_safely(GEOMETRY_FILE, new_lines)

    print(f"\nConverted Cartesian atoms to fractional coordinates.")
    print(f"Overwritten: {GEOMETRY_FILE}")


if __name__ == "__main__":
    main()