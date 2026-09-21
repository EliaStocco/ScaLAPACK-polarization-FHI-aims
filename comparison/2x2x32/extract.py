#!/usr/bin/env python3

import re
from pathlib import Path

import pandas as pd


# =============================================================================
# Adjust this regex to match your FHI-aims timing line
# =============================================================================

TIMING_REGEX = re.compile(
    r"^\s*\|\s*Total time\s*:\s*"
    r"([\d.]+)\s*s\s+"
    r"([\d.]+)\s*s\s*$",
    re.MULTILINE,
)

MEMORY_REGEX = re.compile(
    r"\|\s*Maximum:\s*([\d.]+)\s*MB",
    re.MULTILINE,
)

def extract_peak_memory(outfile):
    """Extract the maximum peak memory (MB) across all tasks."""

    with open(outfile, "r") as f:
        text = f.read()

    matches = MEMORY_REGEX.findall(text)

    if not matches:
        return None  # or raise if you prefer strict behavior

    return max(float(m) for m in matches)

def extract_time(outfile):
    """Extract the wall-clock total time from an FHI-aims output file."""

    with open(outfile, "r") as f:
        text = f.read()

    match = TIMING_REGEX.search(text)

    if not match:
        raise ValueError(f"Could not find total timing in {outfile}")

    cpu_time, wall_time = map(float, match.groups())
    return wall_time


def extract_ncores(filename):
    """Extract ncores from aims.n=XXX.out."""

    match = re.search(r"aims\.n=(\d+)\.out", filename)

    if match is None:
        raise ValueError(f"Could not determine ncores from {filename}")

    return int(match.group(1))


def main():

    records = []

    calculations = ["scf", "dipole"]
    methods = ["lapack", "scalapack"]

    for calculation in calculations:
        for method in methods:

            results_dir = Path(calculation) / method / "results"

            if not results_dir.exists():
                print(f"Skipping missing directory: {results_dir}")
                continue

            for outfile in sorted(results_dir.glob("aims.n=*.out")):

                try:
                    ncores = extract_ncores(outfile.name)
                    time = extract_time(outfile)
                    memory = extract_peak_memory(outfile)

                    if method == "lapack":
                        method = "LAPACK"
                    if method == "scalapack":
                        method = "ScaLAPACK"
                    
                    records.append(
                        {
                            "calculation": calculation,
                            "method": method,
                            "ncores": ncores,
                            "time": time,
                            "peak_memory_mb": memory,
                        }
                    )

                    print(
                        f"{calculation:7s} "
                        f"{method:10s} "
                        f"{ncores:5d} cores "
                        f"{time:.2f} s"
                    )

                except Exception as e:
                    print(f"Failed for {outfile}: {e}")

    df = pd.DataFrame(records)

    df = df.sort_values(
        ["method", "calculation", "ncores"]
    )

    df.to_csv("dataframe.csv", index=False)

    print("\nSaved dataframe.csv")


if __name__ == "__main__":
    main()
