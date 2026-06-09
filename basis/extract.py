import re
from pathlib import Path
import pandas as pd


ROOT = Path(".")

pattern = re.compile(r"aims\.n=(\d+)\.out")


def extract_time(filepath):
    """
    Extract total runtime from an AIMS output file.
    Adjust regex if your format differs.
    """
    with open(filepath, "r") as f:
        for line in f:
            if "Total time" in line:
                match = re.search(r"([\d.]+)", line)
                if match:
                    return float(match.group(1))
    return None


rows = []

# -----------------------------
# Traverse basis sets
# -----------------------------
for basis in ["light", "intermediate", "tight"]:

    for calc in ["dipole", "scf"]:

        results_dir = ROOT / basis / calc / "results"

        if not results_dir.exists():
            continue

        for file in results_dir.glob("aims.n=*.out"):

            m = pattern.search(file.name)
            if not m:
                continue

            ncores = int(m.group(1))
            time = extract_time(file)

            if time is None:
                continue

            rows.append({
                "basis": basis,
                "calculation": calc,
                "ncores": ncores,
                "time": time,
            })


df = pd.DataFrame(rows)
df.to_csv("dataframe.csv",index=False)
df = df.pivot(
    index=["basis", "ncores"],
    columns="calculation",
    values="time"
).reset_index()

df["time"] = df["dipole"] - df["scf"]
df.to_csv("timing.csv",index=False)