#!/usr/bin/env python3
"""Extract net polarization timings and fit t_pol = C * cores**(-p)."""

import csv
import math
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SERIES = {
    ("4x4x4", "LDA"): ("2x2x2", "3 2 2 4", [128, 256, 512, 1024, 2048]),
    ("4x4x4", "HSE06"): ("2x2x2", "3 2 2 4", [128, 256, 512, 1024, 2048]),
    ("8x8x8", "LDA"): ("1x1x1", "3 1 1 2", [256, 512, 1024, 2048]),
    ("8x8x8", "HSE06"): ("1x1x1", "3 1 1 2", [128, 512, 1024]),
}


def total_time(path):
    """Return the wall time from the final detailed time-accounting total."""

    values = []
    for line in path.read_text(errors="replace").splitlines():
        if ":" not in line:
            continue
        label, value_text = line.split(":", 1)
        if label.strip() != "| Total time":
            continue
        values = re.findall(r"[-+]?\d+(?:\.\d+)?", value_text)
        if len(values) >= 2:
            return float(values[-1])
    if not values:
        raise RuntimeError(f"No FHI-aims total time found in {path}")
    raise RuntimeError(f"Could not parse FHI-aims total time in {path}")


def fit(points):
    x = [math.log(n) for n, _ in points]
    y = [math.log(t) for _, t in points]
    xm, ym = sum(x) / len(x), sum(y) / len(y)
    sxx = sum((v - xm) ** 2 for v in x)
    slope = sum((a - xm) * (b - ym) for a, b in zip(x, y)) / sxx
    intercept = ym - slope * xm
    ssres = sum((b - (intercept + slope * a)) ** 2 for a, b in zip(x, y))
    sstot = sum((b - ym) ** 2 for b in y)
    return -slope, math.exp(intercept), 1 - ssres / sstot if sstot else 1.0


def main():
    rows = []
    summaries = []
    for (size, functional), (kgrid, pgrid, cores_list) in SERIES.items():
        points = []
        for cores in cores_list:
            base = ROOT / "raw" / size / functional.lower()
            dipole = base / f"dipole-n{cores}.out"
            scf = base / f"scf-n{cores}.out"
            if not dipole.exists() or not scf.exists():
                continue
            dipole_s = total_time(dipole)
            scf_s = total_time(scf)
            pol_s = dipole_s - scf_s
            rows.append({"supercell": size, "functional": functional,
                         "scf_k_grid": kgrid, "polarization_grid": pgrid,
                         "cores": cores, "scf_seconds": f"{scf_s:.3f}",
                         "dipole_seconds": f"{dipole_s:.3f}",
                         "polarization_seconds": f"{pol_s:.3f}",
                         "dipole_file": str(dipole.relative_to(ROOT)),
                         "scf_file": str(scf.relative_to(ROOT))})
            if pol_s > 0:
                points.append((cores, pol_s))
        if len(points) >= 3:
            p, prefactor, r2 = fit(points)
            summaries.append({"supercell": size, "functional": functional,
                              "scf_k_grid": kgrid, "polarization_grid": pgrid,
                              "n_points": len(points), "p": f"{p:.8f}",
                              "prefactor_seconds": f"{prefactor:.8g}",
                              "R2": f"{r2:.8f}"})

    with (ROOT / "timing_data.csv").open("w", newline="") as handle:
        fields = list(rows[0]) if rows else []
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader(); writer.writerows(rows)
    with (ROOT / "scaling_summary.csv").open("w", newline="") as handle:
        fields = list(summaries[0]) if summaries else []
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader(); writer.writerows(summaries)
    print("Wrote timing_data.csv and scaling_summary.csv")
    for row in summaries:
        print(f"{row['supercell']} {row['functional']}: p={row['p']} R2={row['R2']} ({row['n_points']} points)")


if __name__ == "__main__":
    main()
