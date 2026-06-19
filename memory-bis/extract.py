#!/usr/bin/env python3

import os
import re
import pandas as pd

# Regex for timing
time_pattern = re.compile(
    r"\|\s*| Total time                                  :\s*:\s*([\d.]+)\s*s",
    re.IGNORECASE
)

# Regex for MaxRSS
# memory_pattern = re.compile(
#     r'^\d+\.\d+\s+\S+\s+\d+\s+\d+\s+\d+\s+([\d.]+[KMGT])\s+[\d.]+[KMGT]',
#     re.MULTILINE
# )
memory_pattern = re.compile(
    r"Maximum memory per node:\s*([\d.]+)\s*GB",
    re.IGNORECASE
)


def parse_memory(mem_str):
    """Convert memory string to MB."""
    factors = {
        'K': 1 / 1024,
        'M': 1,
        'G': 1024,
        'T': 1024**2,
    }

    value = float(mem_str[:-1])
    unit = mem_str[-1]

    return value * factors[unit]


results = []

for dirname in os.listdir("."):

    if not (os.path.isdir(dirname) and dirname.startswith("supercell-")):
        continue

    try:
        supercell = int(dirname.split("-")[1])
    except ValueError:
        continue

    for method in ["lapack", "scalapack"]:

        # --------------------
        # Extract timing
        # --------------------
        time_file = os.path.join(dirname, f"{method}.out")

        if not os.path.exists(time_file):
            continue

        timing = None

        with open(time_file) as f:
            for line in f:
                match = time_pattern.search(line)
                if match:
                    timing = float(match.group(1))
                    break

        # --------------------
        # Extract memory
        # --------------------
        memory = None
        mem_file = os.path.join(dirname, f"mem-{method}.out")

        if os.path.exists(mem_file):
            with open(mem_file) as f:
                content = f.read()

            match = memory_pattern.search(content)

            if match:
                memory = float(match.group(1)) # * 1024  # convert GB → MB

        results.append({
            "supercell": supercell,
            "method": method,
            "time_s": timing,
            "memory_mb": memory,
        })


df = pd.DataFrame(results)

df = df.sort_values(
    ["supercell", "method"]
).reset_index(drop=True)

df.to_csv("dataframe.csv", index=False)

print(df)
print("\nSaved to dataframe.csv")