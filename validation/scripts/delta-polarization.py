import numpy as np
import pandas as pd
import argparse
import ast

parser = argparse.ArgumentParser()
parser.add_argument("-i", "--input", type=str, required=True)
parser.add_argument("-o", "--output", type=str, required=True)
args = parser.parse_args()

df = pd.read_csv(args.input)

def parse(x):
    return np.array(ast.literal_eval(x), dtype=float)

def wrap_frac(x):
    return x - np.round(x)

results = []

for (sys, xc, spin), block in df.groupby(["system", "xc", "spin"]):

    sc_block = block[block["implementation"] == "scalapack"]

    if sc_block.empty:
        print(f"Missing scalapack: sys={sys}, xc={xc}, spin={spin}")
        continue

    if sc_block["state"].nunique() != 2:
        print(
            f"Expected 2 states, got "
            f"{sc_block['state'].nunique()} "
            f"for sys={sys}, xc={xc}, spin={spin}"
        )
        continue

    state_map = {}

    # ---------------------------------------------------------
    # Build wrapped dipoles for each state
    # ---------------------------------------------------------
    for _, row in sc_block.iterrows():

        if pd.isna(row["polarization"]) or pd.isna(row["cell"]):
            continue

        state = row["state"]

        cell = np.array(ast.literal_eval(row["cell"]), dtype=float)
        P = parse(row["polarization"])/1000

        V = float(np.linalg.det(cell))

        # dipole in Cartesian coordinates
        d_cart = P * V

        # fractional dipole coordinates
        d_lat = np.linalg.solve(cell.T, d_cart)

        # wrap into [-0.5, 0.5]
        d_lat_wrapped = d_lat # wrap_frac(d_lat)

        # back to Cartesian
        d_cart_wrapped = cell.T @ d_lat_wrapped

        state_map[state] = {
            "cell": cell,
            "volume": V,
            "P": P,
            "d_cart": d_cart_wrapped,
        }

    if len(state_map) != 2:
        print(f"Incomplete data: sys={sys}, xc={xc}, spin={spin}")
        continue

    states = list(state_map.keys())
    s1, s2 = states[0], states[1]

    # ---------------------------------------------------------
    # Extract data
    # ---------------------------------------------------------
    P1 = state_map[s1]["P"]
    P2 = state_map[s2]["P"]

    V1 = state_map[s1]["volume"]
    V2 = state_map[s2]["volume"]

    cell1 = state_map[s1]["cell"]
    cell2 = state_map[s2]["cell"]

    d1 = state_map[s1]["d_cart"]
    d2 = state_map[s2]["d_cart"]

    # ---------------------------------------------------------
    # Dipole difference
    # ---------------------------------------------------------
    delta = d2 - d1

    # lattice representations
    delta_lat1 = np.linalg.solve(cell1.T, delta)
    delta_lat2 = np.linalg.solve(cell2.T, delta)

    # polarization differences reconstructed
    delta_P_cart1 = delta / V1
    delta_P_cart2 = delta / V2

    # raw polarization difference
    delta_P_raw = P2 - P1

    results.append({
        "system": sys,
        "xc": xc,
        "spin": spin,
        "state1": s1,
        "state2": s2,

        "delta_dipole_cart": (1000*delta).tolist(),

        "delta_dipole_lat_state1": (1000*delta_lat1).tolist(),
        "delta_dipole_lat_state2": (1000*delta_lat2).tolist(),

        "delta_P_from_V1": (1000*delta_P_cart1).tolist(),
        "delta_P_from_V2": (1000*delta_P_cart2).tolist(),

        "delta_P_raw": (1000*delta_P_raw).tolist(),
    })

out_df = pd.DataFrame(results)
out_df.to_csv(args.output, index=False)