from pathlib import Path
import re
import numpy as np
import pandas as pd


def extract_aims_data(path):
    """Extract polarization k-grid and Cartesian polarization from aims.out."""

    text = path.read_text(errors="replace")

    # ------------------------------------------------------------
    # 1. Extract the three "output polarization" rows
    #
    # Example:
    # output polarization    1 80  2  2
    # output polarization    2  2 80  2
    # output polarization    3  2  2 80
    # ------------------------------------------------------------

    pol_rows = re.findall(
        r"^\s*output\s+polarization\s+([123])\s+(\d+)\s+(\d+)\s+(\d+)\s*$",
        text,
        flags=re.MULTILINE | re.IGNORECASE,
    )

    if len(pol_rows) != 3:
        raise ValueError(
            f"{path}: expected exactly 3 'output polarization' rows, "
            f"found {len(pol_rows)}"
        )

    grid = {}

    for component, a, b, c in pol_rows:
        grid[int(component)] = (int(a), int(b), int(c))

    if set(grid) != {1, 2, 3}:
        raise ValueError(
            f"{path}: expected polarization components 1, 2, 3; "
            f"found {sorted(grid)}"
        )

    # ------------------------------------------------------------
    # 2. Collect ALL six off-diagonal values
    # ------------------------------------------------------------

    off_diagonal = [
        grid[1][1],
        grid[1][2],
        grid[2][0],
        grid[2][2],
        grid[3][0],
        grid[3][1],
    ]

    # Make sure every off-diagonal value is identical
    if len(set(off_diagonal)) != 1:
        raise ValueError(
            f"{path}: off-diagonal k-grid values are not equal: "
            f"{off_diagonal}"
        )

    k_grid = off_diagonal[0]

    # ------------------------------------------------------------
    # 3. Extract Cartesian polarization
    #
    # Example:
    # | Cartesian Polarization   322.264451E-03 ...
    # ------------------------------------------------------------

    match = re.search(
        r"^\s*\|\s*Cartesian\s+Polarization\s+"
        r"([+-]?\d+(?:\.\d*)?(?:[Ee][+-]?\d+)?)\s+"
        r"([+-]?\d+(?:\.\d*)?(?:[Ee][+-]?\d+)?)\s+"
        r"([+-]?\d+(?:\.\d*)?(?:[Ee][+-]?\d+)?)",
        text,
        flags=re.MULTILINE | re.IGNORECASE,
    )

    if match is None:
        raise ValueError(
            f"{path}: could not find Cartesian Polarization"
        )

    px, py, pz = map(float, match.groups())

    # ------------------------------------------------------------
    # 4. Polarization norm
    # ------------------------------------------------------------

    polarization_norm = np.sqrt(px**2 + py**2 + pz**2)

    return {
        "k_grid": k_grid,
        "polarization_x": px,
        "polarization_y": py,
        "polarization_z": pz,
        "polarization_norm": polarization_norm,
    }


# ================================================================
# Main
# ================================================================

root = Path(".")

rows = []

# Folder name -> value to put in the "spline" column
groups = {
    "wo_spline": "no",
    "w_spline": "yes",
}

for folder, spline_value in groups.items():

    base = root / folder

    if not base.exists():
        raise FileNotFoundError(f"Directory not found: {base}")

    # Find every aims.out one level below the group directory
    for aims_file in sorted(base.glob("*/aims.out")):
        # print(aims_file)

        try:
            data = extract_aims_data(aims_file)

            rows.append({
                "file" : aims_file,
                "spline": spline_value,
                **data,
            })

        except Exception as exc:
            print(f"ERROR processing {aims_file}")
            raise


# ================================================================
# Create DataFrame
# ================================================================

df = pd.DataFrame(rows)

# Sort first by spline and then numerically by k_grid
df = (
    df
    .sort_values(["spline", "k_grid"])
    .reset_index(drop=True)
)

df.to_csv("dataframe.csv",index=False)