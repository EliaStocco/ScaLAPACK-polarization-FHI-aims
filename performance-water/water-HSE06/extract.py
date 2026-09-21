"""Extract total CPU times from the HSE06 scaling calculations.

Run this script from this directory.  It writes ``dataframe.csv``, which is
consumed by ``fit-dataframe.py`` and ``plot.py``.
"""

import re
from pathlib import Path

import pandas as pd


TIME_PATTERN = re.compile(
    r"\| Total time\s+:\s*([\d.]+)\s+s\s+[\d.]+\s+s"
)

results = []

for outfile in Path(".").glob("*-HSE06/results/aims.n=*.out"):
    calculation = outfile.parts[0].removesuffix("-HSE06")
    ncores = int(outfile.stem.split("=")[1])

    runtime = None
    with outfile.open() as handle:
        for line in handle:
            match = TIME_PATTERN.search(line)
            if match:
                # The first column in FHI-aims' final timing summary is CPU time.
                runtime = float(match.group(1))

    if runtime is None:
        raise ValueError(f"Could not find the final total time in {outfile}")

    results.append(
        {
            "calculation": calculation,
            "ncores": ncores,
            "time": runtime,
        }
    )

if not results:
    raise FileNotFoundError("No *-HSE06/results/aims.n=*.out files found")

df = pd.DataFrame(results).sort_values(["calculation", "ncores"])
df.to_csv("dataframe.csv", index=False)
