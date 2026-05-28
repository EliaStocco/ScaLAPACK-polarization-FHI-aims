import numpy as np
import pandas as pd
import argparse
import ast

parser = argparse.ArgumentParser()
parser.add_argument("-i", "--input", type=str, required=True)
args = parser.parse_args()

df = pd.read_csv(args.input)

for (sys, xc, state, spin), block in df.groupby(
    ["system", "xc", "state", "spin"]
):
    # ensure we have both implementations
    lapack = block[block["implementation"] == "lapack"]["polarization"]
    scalapack = block[block["implementation"] == "scalapack"]["polarization"]

    if lapack.empty or scalapack.empty  or pd.isna(lapack.iloc[0]) or pd.isna(scalapack.iloc[0]):
        print(f"Missing data: sys={sys}, xc={xc}, state={state}, spin={spin}")
        continue

    # assuming one entry per implementation
    p_lapack = np.array(ast.literal_eval(lapack.iloc[0]))
    p_scalapack = np.array(ast.literal_eval(scalapack.iloc[0]))

    if not np.allclose(p_lapack, p_scalapack, atol=1e-6):
        print("Mismatch detected:")
        print(f"sys={sys}, xc={xc}, state={state}, spin={spin}")
        print("lapack   :", p_lapack)
        print("scalapack:", p_scalapack)