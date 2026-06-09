import re
from pathlib import Path
import pandas as pd

results = []

for outfile in Path(".").glob("*/**/aims.n=*.out"):
    m = outfile.parts[0]# .split("=")[1]        # 128, 196
    calculation = outfile.parts[1]            # scf, dipole
    ncores = outfile.stem.split("=")[1]       # 128, 256, ...

    runtime = None

    with open(outfile) as f:
        for line in f:
            if "Total time" in line:
                match = re.search(r'([\d.]+)\s*(?:s|seconds)', line)
                if match:
                    runtime = float(match.group(1))

    results.append({
        "supercell": int(m[0]),
        "calculation": calculation,
        "ncores": int(ncores),
        "time": runtime,
    })

df = pd.DataFrame(results)
df = df.sort_values(["supercell", "calculation", "ncores"])
df.to_csv("dataframe.csv",index=False)