import numpy as np
import re
import pandas as pd
import argparse
from ase.io import read
from tqdm import tqdm

def extract_float(string: str) -> np.ndarray:
    """
    Extract all floats from a string (scientific notation).
    """
    elements = re.findall(r'[-+]?\d*\.\d+E[+-]?\d+', string)
    if not elements:
        raise ValueError("no float found")
    return np.asarray([float(a) for a in elements])


parser = argparse.ArgumentParser()
parser.add_argument("-i", "--input", type=str, required=True, help="input CSV file.")
parser.add_argument("-o", "--output", type=str, required=True, help="output CSV file.")
args = parser.parse_args()

df = pd.read_csv(args.input)

# new columns
df["polarization"] = None
df["cell"] = None
df["quanta"] = None

# constants
e = 1.602176634e-19   # C
angstrom = 1e-10      # m

for idx, row in tqdm(df.iterrows(), total=len(df), desc="Processing files"):
    file = row["file"]
    if pd.isna(file):
        continue

    atoms = None

    # ---- read structure ----
    try:
        atoms = read(file, index=0, format='aims-output')
        cell_ang = atoms.cell.array          # Å
        df.at[idx, "cell"] = cell_ang.tolist()

        # ---- polarization quantum (C/m^2) ----
        cell = atoms.cell.array * angstrom   # m
        volume = np.abs(np.linalg.det(cell))  # m^3

        # polarization quantum magnitudes along lattice vectors
        quanta = 1000* (e / volume) * np.linalg.norm(cell, axis=1)  # shape (3,)
        
        df.at[idx, "quanta"] = quanta.tolist()
        print(file,quanta)

    except Exception as e1:
        print(f"[CELL ERROR] {file}: {e1}")

    # ---- read polarization ----
    try:
        with open(file, "r") as f:
            found = False
            for line in reversed(f.readlines()):
                if "| Cartesian Polarization" in line:
                    polarization = extract_float(line)
                    if polarization.shape != (3,):
                        raise ValueError("Polarization is not 3-component")

                    # stored as in your original script
                    df.at[idx, "polarization"] = (1000 * polarization).tolist()
                    found = True
                    break

            if not found:
                print(f"[WARNING] Polarization not found in '{file}'")

    except Exception as e2:
        print(f"[POL ERROR] {file}: {e2}")

df.to_csv(args.output, index=False)