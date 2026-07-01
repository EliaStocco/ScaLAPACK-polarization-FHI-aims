import re
from pathlib import Path
import pandas as pd

results = []

for outfile in Path(".").glob("*/**/aims.n=*.out"):
    m = outfile.parts[0]
    calculation = outfile.parts[1]
    ncores = outfile.stem.split("=")[1]

    runtime = None

    with open(outfile) as f:
        for line in f:
            if "| Total time                                  :" in line:
                match = re.search(r'([\d.]+)\s*(?:s|seconds)', line)
                if match:
                    runtime = float(match.group(1))
                    break

    results.append({
        "supercell": int(m[0]),
        "calculation": calculation,
        "ncores": int(ncores),
        "time": runtime,
    })

df = pd.DataFrame(results)

# Remove entries for which the runtime could not be extracted
df = df.dropna(subset=["time"])

df = df.sort_values(["supercell", "calculation", "ncores"])
df.to_csv("dataframe.csv", index=False)