import re
from pathlib import Path
import pandas as pd

results = []

for outfile in Path(".").glob("m=*/dipole/aims.n=*.out"):
    m = int(outfile.parts[0].split("=")[1])
    # calculation = outfile.parts[1]
    ncores = int(outfile.stem.split("=")[1])

    runtime = None

    with open(outfile) as f:
        for line in f:
            # "Total Time for dipole matrix"
            # "Total Time for dipole term"
            if "Total Time for Fourier interpolated EV solution" in line:
                match = re.search(
                    r"Total Time for Fourier interpolated EV solution\s*:\s*([\d.]+)\s+([\d.]+)",
                    line
                )

                if match:
                    runtime = float(match.group(2))  # second timing value
                    break  # stop after finding the timing

    results.append({
        "molecules": m,
        # "calculation": calculation,
        "ncores": ncores,
        "time": runtime,
    })

df = pd.DataFrame(results)
df = df.sort_values(["molecules", "ncores"])

print(df)

df.to_csv("dataframe.csv", index=False)