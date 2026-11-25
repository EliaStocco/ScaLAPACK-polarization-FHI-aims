#!/usr/bin/env python3
"""Extract Viper net-polarization timings and fit ``t = C * cores**(-p)``."""

from __future__ import annotations

import csv
import math
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parent
TOTAL_TIME = re.compile(
    r"^\s*\|\s+Total time\s+:\s+([0-9.]+) s\s+([0-9.]+) s\s*$",
    re.MULTILINE,
)
SERIES = (
    ("4x4x4", "LDA", "2x2x2", "3 2 2 4", (128, 256, 512, 1024, 2048)),
    ("4x4x4", "HSE06", "2x2x2", "3 2 2 4", (128, 256, 512, 1024, 2048)),
    ("8x8x8", "LDA", "1x1x1", "3 1 1 2", (256, 512, 1024, 2048)),
    ("8x8x8", "HSE06", "1x1x1", "3 1 1 2", (128, 256, 512, 1024, 2048)),
)


def total_time(path: Path) -> float:
    """Return the final detailed whole-run wall time from an FHI-aims output."""

    matches = TOTAL_TIME.findall(path.read_text(errors="replace"))
    if not matches:
        raise RuntimeError(f"No final detailed total time found in {path}")
    return float(matches[-1][1])


def dipole_path(size: str, functional: str, cores: int) -> Path:
    if size == "4x4x4":
        directory = "hse06" if functional == "HSE06" else "lda"
        name = f"aims.grid3224.n={cores}.out"
    elif functional == "LDA":
        directory = "lda"
        name = f"aims.grid3112.n={cores}.out"
    else:
        directory = "hse06-unconverged"
        name = f"aims.grid3112-unconverged.n={cores}.out"
    return ROOT / "raw" / size / directory / "dipole" / f"n={cores}" / name


def scf_path(size: str, functional: str, cores: int) -> Path:
    if size == "4x4x4":
        directory = "hse06" if functional == "HSE06" else "lda"
        if functional == "HSE06" and cores in (128, 512):
            name = f"aims.repeat-20261101.n={cores}.out"
        else:
            name = f"aims.n={cores}.out"
    elif functional == "LDA":
        directory = "lda"
        name = f"aims.n={cores}.out"
    else:
        directory = "hse06-unconverged"
        if cores in (128, 256):
            name = f"aims.hugemem-20261101.n={cores}.out"
        else:
            name = f"aims.scf.n={cores}.out"
    return ROOT / "raw" / size / directory / "scf" / f"n={cores}" / name


def fit(points: list[tuple[int, float]]) -> tuple[float, float, float]:
    x = [math.log(cores) for cores, _ in points]
    y = [math.log(time) for _, time in points]
    x_mean = sum(x) / len(x)
    y_mean = sum(y) / len(y)
    slope = sum((a - x_mean) * (b - y_mean) for a, b in zip(x, y))
    slope /= sum((value - x_mean) ** 2 for value in x)
    intercept = y_mean - slope * x_mean
    residual = sum((value - (intercept + slope * point)) ** 2 for point, value in zip(x, y))
    total = sum((value - y_mean) ** 2 for value in y)
    return -slope, math.exp(intercept), 1 - residual / total if total else 1.0


def main() -> None:
    rows = []
    summaries = []
    for size, functional, k_grid, p_grid, cores_list in SERIES:
        points = []
        for cores in cores_list:
            dipole = dipole_path(size, functional, cores)
            scf = scf_path(size, functional, cores)
            dipole_seconds = total_time(dipole)
            scf_seconds = total_time(scf)
            polarization_seconds = dipole_seconds - scf_seconds
            rows.append(
                {
                    "supercell": size,
                    "functional": functional,
                    "scf_k_grid": k_grid,
                    "polarization_grid": p_grid,
                    "cores": cores,
                    "scf_seconds": f"{scf_seconds:.3f}",
                    "dipole_seconds": f"{dipole_seconds:.3f}",
                    "polarization_seconds": f"{polarization_seconds:.3f}",
                    "dipole_file": str(dipole.relative_to(ROOT)),
                    "scf_file": str(scf.relative_to(ROOT)),
                }
            )
            points.append((cores, polarization_seconds))
        exponent, prefactor, r_squared = fit(points)
        summaries.append(
            {
                "supercell": size,
                "functional": functional,
                "scf_k_grid": k_grid,
                "polarization_grid": p_grid,
                "n_points": len(points),
                "p": f"{exponent:.8f}",
                "prefactor_seconds": f"{prefactor:.8g}",
                "R2": f"{r_squared:.8f}",
            }
        )

    for filename, data in (("timing_data.csv", rows), ("scaling_summary.csv", summaries)):
        with (ROOT / filename).open("w", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(data[0]))
            writer.writeheader()
            writer.writerows(data)
    print("Wrote timing_data.csv and scaling_summary.csv")
    for summary in summaries:
        print(
            f"{summary['supercell']} {summary['functional']}: "
            f"p={summary['p']} R2={summary['R2']} ({summary['n_points']} points)"
        )


if __name__ == "__main__":
    main()
