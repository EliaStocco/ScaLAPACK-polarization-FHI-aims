#!/usr/bin/env python3

import re
from pathlib import Path

import pandas as pd


# =============================================================================
# Adjust this regex to match your FHI-aims timing line
# =============================================================================

TIMING_REGEX = re.compile(
    r"Total time\s*:\s*([\d.]+)\s*s"
)

# Examples:
#
# TIMING_REGEX = re.compile(
#     r"\|\s*Total time\s*:\s*([\d.]+)\s*s"
# )
#
# TIMING_REGEX = re.compile(
#     r"Total wall clock time\s*:\s*([\d.]+)"
# )


def extract_time(outfile):
    """Extract total time from an aims output file."""

    with open(outfile, "r") as f:
        text = f.read()

    matches = TIMING_REGEX.findall(text)

    if not matches:
        raise ValueError(f"Could not find timing in {outfile}")

    return float(matches[-1])


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

                    records.append(
                        {
                            "calculation": calculation,
                            "method": method,
                            "ncores": ncores,
                            "time": time,
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
