#!/usr/bin/env python3
"""Extract wall times from all SCF and polarization calculations.

Run this script from any directory.  The CSV is always written next to this
script, so the rest of the analysis pipeline can use it without relying on
the current working directory.
"""

from __future__ import annotations

import re
import csv
from pathlib import Path

HERE = Path(__file__).resolve().parent
TIME_PATTERN = re.compile(r"\| Total time\s*:\s*([0-9.]+)\s*s")
COMPONENT_PATTERNS = {
    "wannier_time_s": re.compile(
        r"\|\s*Total time for Wannier Center Evolution\s*:\s*"
        r"[\d.eE+-]+\s*s\s+([\d.eE+-]+)\s*s"
    ),
    "fourier_ev_time_s": re.compile(
        r"\|\s*Total Time for Fourier interpolated EV solution\s*:\s*"
        r"[\d.eE+-]+\s+([\d.eE+-]+)"
    ),
    "dipole_matrix_time_s": re.compile(
        r"\|\s*Total Time for dipole matrix\s*:\s*"
        r"[\d.eE+-]+\s+([\d.eE+-]+)"
    ),
    "dipole_term_time_s": re.compile(
        r"\|\s*Total Time for dipole term\s*:\s*"
        r"[\d.eE+-]+\s+([\d.eE+-]+)"
    ),
    "berry_term_time_s": re.compile(
        r"\|\s*Total Time for berry term\s*:\s*"
        r"[\d.eE+-]+\s+([\d.eE+-]+)"
    ),
}


def parse_runtime(outfile: Path) -> float:
    """Return the reported total wall time from an FHI-aims output file."""

    runtime = None
    for line in outfile.read_text(errors="replace").splitlines():
        match = TIME_PATTERN.search(line)
        if match:
            runtime = float(match.group(1))

    if runtime is None:
        raise ValueError(f"No '| Total time :' entry found in {outfile}")
    return runtime


def parse_component_times(outfile: Path) -> dict[str, float]:
    """Return summed wall times for all three polarization directions."""

    text = outfile.read_text(errors="replace")
    component_times = {}
    for name, pattern in COMPONENT_PATTERNS.items():
        values = [float(value) for value in pattern.findall(text)]
        if not values:
            raise ValueError(f"No {name} entries found in {outfile}")
        component_times[name] = sum(values)
    return component_times


def main() -> None:
    records = []
    failures = []

    for outfile in sorted(HERE.glob("m=*/xc=*/*/aims.n=*.out")):
        m_dir, xc_dir, calculation, filename = outfile.relative_to(HERE).parts

        try:
            molecules = int(m_dir.removeprefix("m="))
            functional = xc_dir.removeprefix("xc=")
            ncores = int(filename.removeprefix("aims.n=").removesuffix(".out"))
            runtime = parse_runtime(outfile)
            component_times = (
                parse_component_times(outfile) if calculation == "dipole" else {}
            )
        except (ValueError, IndexError) as error:
            failures.append(str(error))
            continue

        records.append({
            "molecules": molecules,
            "functional": functional,
            "calculation": calculation,
            "ncores": ncores,
            "time_s": runtime,
            **component_times,
            "file": str(outfile.relative_to(HERE)),
        })

    if failures:
        raise SystemExit("\n".join(failures))
    if not records:
        raise SystemExit("No output files matching m=*/xc=*/*/aims.n=*.out were found.")

    records.sort(key=lambda row: (row["functional"], row["molecules"], row["calculation"], row["ncores"]))
    output = HERE / "dataframe.csv"
    with output.open("w", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "molecules", "functional", "calculation", "ncores", "time_s",
                *COMPONENT_PATTERNS, "file",
            ],
        )
        writer.writeheader()
        writer.writerows(records)
    print(f"Wrote {len(records)} timing records to {output}")


if __name__ == "__main__":
    main()
