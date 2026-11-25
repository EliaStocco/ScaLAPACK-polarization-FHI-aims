#!/usr/bin/env python3
"""Extract dense-LDA component timings from bundled FHI-aims outputs."""

from __future__ import annotations

import csv
import re
from collections import defaultdict
from pathlib import Path


HERE = Path(__file__).resolve().parent
RAW = HERE / "dense_raw"
OUTPUT = HERE / "dense_component_data.csv"

TOTAL = re.compile(r"^\s*\|\s*Total time\s*:\s*([\d.eE+-]+)\s*s", re.MULTILINE)
PATTERNS = {
    "fourier_interpolation_time_s": re.compile(
        r"\|\s*Total Time for Fourier interpolated EV solution\s*:\s*([\d.eE+-]+)"
    ),
    "dipole_matrix_time_s": re.compile(
        r"\|\s*Total Time for dipole matrix\s*:\s*([\d.eE+-]+)"
    ),
    "dipole_term_time_s": re.compile(
        r"\|\s*Total Time for dipole term\s*:\s*([\d.eE+-]+)"
    ),
    "berry_term_time_s": re.compile(
        r"\|\s*Total Time for berry term\s*:\s*([\d.eE+-]+)"
    ),
}


def parse(path: Path, components: bool = False) -> dict[str, float]:
    text = path.read_text(errors="replace")
    match = TOTAL.search(text)
    if match is None:
        raise ValueError(f"no total time in {path}")
    result = {"time_s": float(match.group(1))}
    if components:
        for name, pattern in PATTERNS.items():
            values = [float(value) for value in pattern.findall(text)]
            if not values:
                raise ValueError(f"no {name} in {path}")
            result[name] = sum(values)
    return result


def main() -> None:
    runs: dict[tuple[str, int], dict[str, dict[str, float]]] = defaultdict(dict)
    for path in RAW.glob("*x*x*/**/aims.n=*.out"):
        supercell, calculation, filename = path.relative_to(RAW).parts
        cores = int(filename.removeprefix("aims.n=").removesuffix(".out"))
        try:
            runs[(supercell, cores)][calculation] = parse(
                path, components=calculation == "dipole"
            )
        except ValueError as error:
            print(f"[WARN] Skipping {path.relative_to(RAW)}: {error}")

    fields = [
        "series_id", "supercell", "cores", "polarization_time_s",
        *PATTERNS,
    ]
    rows = []
    for (supercell, cores), calculations in sorted(runs.items()):
        if not {"scf", "dipole"} <= calculations.keys():
            continue
        scf = calculations["scf"]
        dipole = calculations["dipole"]
        row = {
            "series_id": f"{supercell}_lda_dense",
            "supercell": supercell,
            "cores": cores,
            "polarization_time_s": dipole["time_s"] - scf["time_s"],
            **{name: dipole[name] for name in PATTERNS},
        }
        rows.append(row)
    with OUTPUT.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    print(f"Wrote {OUTPUT} ({len(rows)} paired runs)")


if __name__ == "__main__":
    main()
