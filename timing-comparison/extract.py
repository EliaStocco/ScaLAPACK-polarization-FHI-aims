#!/usr/bin/env python3

import re
from pathlib import Path
import pandas as pd


# --------------------------------------------------
# Extract LAST float from "Total time" line
# --------------------------------------------------
def extract_total_time(filepath):
    with open(filepath, "r", errors="ignore") as f:
        for line in f:
            if "| Total time" in line:
                nums = re.findall(r"[\d.]+", line)
                if nums:
                    return float(nums[-1])  # <-- last number (SCALAPACK case)
    raise ValueError(f"No 'Total time' found in {filepath}")


# --------------------------------------------------
# Find aims.out safely (ignore backups like ~aims.out)
# --------------------------------------------------
def find_aims_out(folder):
    candidates = list(folder.glob("aims.out"))
    candidates += list(folder.glob("*aims*.out"))

    # remove backups
    candidates = [c for c in candidates if "~" not in c.name]

    return candidates[0] if candidates else None


# --------------------------------------------------
# Main
# --------------------------------------------------
def main():

    base = Path(".")

    rows = []

    for sc_dir in sorted(base.glob("supercell-*")):

        if not sc_dir.is_dir():
            continue

        supercell = int(sc_dir.name.replace("supercell-", ""))

        for method in ["lapack", "scalapack"]:

            run_dir = sc_dir / method

            if not run_dir.exists():
                continue

            aims_out = find_aims_out(run_dir)

            if aims_out is None:
                print(f"[WARN] Missing aims.out in {run_dir}")
                continue

            try:
                time = extract_total_time(aims_out)

                rows.append({
                    "supercell": supercell,
                    "method": method,
                    "time": time,
                })

                print(f"supercell {supercell:>3} | {method:10s} | {time:.3f} s")

            except Exception as e:
                print(f"[ERROR] {run_dir}: {e}")

    df = pd.DataFrame(rows)

    df = df.sort_values(["supercell", "method"])

    df.to_csv("dataframe.csv", index=False)

    print("\nSaved dataframe.csv")


if __name__ == "__main__":
    main()