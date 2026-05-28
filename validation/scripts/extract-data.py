import numpy as np
import re
import pandas as pd
import argparse
from ase.io import read
from tqdm import tqdm

def extract_float(string:str)->np.ndarray:
    """
    Extract all the float from a string
    """
    elments = re.findall(r'[-+]?\d*\.\d+E[+-]?\d+', string)
    if elments is None or len(elments) == 0:
        raise ValueError("no float found")
    return np.asarray([float(a) for a in elments])

parser = argparse.ArgumentParser()
parser.add_argument("-i", "--input" , type=str, required=True, help="input CSV file.")
parser.add_argument("-o", "--output", type=str, required=True, help="output CSV file.")
args = parser.parse_args()

df = pd.read_csv(args.input)
# create a new column
df["polarization"] = None
df["cell"] = None

for idx, row in tqdm(df.iterrows(), total=len(df), desc="Processing files"):
    file = row["file"]
    if pd.isna(file):
        continue
    
    try:
        atoms = read(file,index=0,format='aims-output')
        df.at[idx, "cell"] = atoms.cell.array.tolist()
    except:
        pass

    with open(file, "r") as f:
        found = False
        for line in reversed(f.readlines()):
            if "| Cartesian Polarization" in line:
                polarization = extract_float(line)
                assert polarization.shape == (3,)
                
                # store as list (or tuple) so it fits in a CSV
                df.at[idx, "polarization"] = (1000*polarization).tolist()
                found = True
                break
        if not found:
            print(f"Polarization not found in file '{file}'")

df.to_csv(args.output, index=False)
    