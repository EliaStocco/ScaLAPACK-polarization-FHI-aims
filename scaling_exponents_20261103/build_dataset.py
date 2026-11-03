#!/usr/bin/env python3
"""Extract FHI-aims timings and fit dipole-minus-SCF scaling laws.

Run from this bundle directory:
    python3 build_dataset.py

It writes timing_data.csv, scaling_summary.csv, and raw_files_manifest.csv.
The summary also includes log--log fits for four FHI-aims polarization components.
"""

import csv
import math
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parent
RAW = ROOT / "raw"
TOTAL_TIME = re.compile(
    r"^\s*\|\s+Total time\s+:\s+([0-9.]+) s\s+([0-9.]+) s\s*$",
    re.MULTILINE,
)
COMPONENT_TIME = re.compile(
    r"^\s*\|\s+Total Time for (Fourier interpolated EV solution|dipole matrix|berry term|dipole term)\s+:\s+([0-9.]+)\s+([0-9.]+)\s*$",
    re.MULTILINE,
)
COMPONENTS = {
    "fourier_interpolation": "Fourier interpolated EV solution",
    "dipole_matrix": "dipole matrix",
    "berry_term": "berry term",
    "dipole_term": "dipole term",
}
PEAK_TRACKED_MEMORY = re.compile(
    r"Peak value(?:s)? for overall tracked memory usage:.*?"
    r"\|\s+Maximum:\s+([0-9.]+) MB",
    re.DOTALL,
)
PARTITION_MEMORY_MB = {"normalmem": 480000.0, "largemem": 980000.0, "hugemem": 2250000.0}


def total_time(relative_path: str) -> float:
    """Return FHI-aims' final maximum total time (seconds)."""
    path = RAW / relative_path
    values = TOTAL_TIME.findall(path.read_text(errors="replace"))
    if not values:
        raise RuntimeError(f"Could not find final total time in {path}")
    return float(values[-1][1])


def component_times(relative_path: str) -> dict[str, float]:
    """Return final maximum wall times for the four polarization components."""
    path = RAW / relative_path
    timings = {
        label: float(wall)
        for label, _cpu, wall in COMPONENT_TIME.findall(path.read_text(errors="replace"))
    }
    missing = set(COMPONENTS.values()) - set(timings)
    if missing:
        raise RuntimeError(f"Missing component timings {sorted(missing)} in {path}")
    return {field: timings[label] for field, label in COMPONENTS.items()}


def peak_tracked_memory_mb(relative_path: str) -> float:
    """Return the largest FHI-aims tracked-memory maximum (MB per MPI rank)."""
    path = RAW / relative_path
    values = [float(value) for value in PEAK_TRACKED_MEMORY.findall(path.read_text(errors="replace"))]
    if not values:
        raise RuntimeError(f"Could not find peak tracked memory in {path}")
    return max(values)


def peak_memory_partition(series: dict, cores: int) -> str:
    """Return the Slurm feature of the run holding this series' peak memory."""
    if series["series_id"].startswith("8x8x8_hse06") and cores == 128:
        return "hugemem"
    if "largemem" in series["resource_class"]:
        return "largemem"
    return "normalmem"


def nodes_partition_summary(series: dict) -> str:
    """Compact mapping of MPI rank count to requested nodes and memory feature."""
    if series["series_id"].startswith("8x8x8_hse06"):
        return "128: 1 hugemem; 512/1024/2048: 4/8/16 largemem"
    partition = "largemem" if "largemem" in series["resource_class"] else "normalmem"
    rank_text = "/".join(str(cores) for cores in series["cores"])
    node_text = "/".join(str(cores // 128) for cores in series["cores"])
    return f"{rank_text}: {node_text} {partition}"


def hms(seconds: float) -> str:
    seconds = round(seconds)
    hours, seconds = divmod(seconds, 3600)
    minutes, seconds = divmod(seconds, 60)
    if hours:
        return f"{hours} h {minutes:02d} m {seconds:02d} s"
    if minutes:
        return f"{minutes} m {seconds:02d} s"
    return f"{seconds} s"


def fit_loglog(rows: list[dict], value_key: str = "polarization_time_s") -> tuple[float, float]:
    """Fit ln(value) = intercept + alpha*ln(cores)."""
    x = [math.log(row["cores"]) for row in rows]
    y = [math.log(row[value_key]) for row in rows]
    x_mean = sum(x) / len(x)
    y_mean = sum(y) / len(y)
    alpha = sum((xi - x_mean) * (yi - y_mean) for xi, yi in zip(x, y))
    alpha /= sum((xi - x_mean) ** 2 for xi in x)
    residual = sum((yi - (y_mean + alpha * (xi - x_mean))) ** 2 for xi, yi in zip(x, y))
    total = sum((yi - y_mean) ** 2 for yi in y)
    return alpha, 1.0 - residual / total


def fit_power_law(rows: list[dict], value_key: str = "polarization_time_s") -> tuple[float, float, float]:
    """Return signed slope, intercept, and R² for ln(value) vs ln(cores)."""
    alpha, r_squared = fit_loglog(rows, value_key)
    x_mean = sum(math.log(row["cores"]) for row in rows) / len(rows)
    y_mean = sum(math.log(row[value_key]) for row in rows) / len(rows)
    return alpha, y_mean - alpha * x_mean, r_squared


def path_4_lda_3644_dipole(n: int) -> str:
    return f"4x4x4/dipole/n={n}/aims.direction3.n={n}.out"


def path_4_lda_scf(n: int) -> str:
    return f"4x4x4/scf/n={n}/aims.n={n}.out"


def path_4_hse_3644_dipole(n: int) -> str:
    return f"4x4x4/hse06/dipole/n={n}/aims.n={n}.out"


def path_4_hse_scf(n: int) -> str:
    return f"4x4x4/hse06/scf/n={n}/aims.n={n}.out"


def path_4_lda_3422_dipole(n: int) -> str:
    return f"4x4x4/dipole-grid-3-4-2-2/lda/n={n}/aims.grid3422.n={n}.out"


def path_4_hse_3422_paired_dipole(n: int) -> str:
    return f"4x4x4/paired-hse06-grid3422/n={n}/dipole/aims.paired-20261102.dipole.n={n}.out"


def path_4_hse_3422_paired_scf(n: int) -> str:
    return f"4x4x4/paired-hse06-grid3422/n={n}/scf/aims.paired-20261102.scf.n={n}.out"


def path_8_lda_scf(n: int) -> str:
    return f"8x8x8/scf/n={n}/aims.n={n}.out"


def path_8_lda_3322_dipole(n: int) -> str:
    if n == 128:
        return "8x8x8/dipole-largemem/n=128/aims.grid3322-rerun.n=128.out"
    return f"8x8x8/dipole-largemem/n={n}/aims.n={n}.out"


def path_8_lda_3211_dipole(n: int) -> str:
    return f"8x8x8/dipole-grid-3-2-1-1/lda/n={n}/aims.grid3211.n={n}.out"


def path_8_hse_scf(n: int) -> str:
    if n == 128:
        return "8x8x8/hse06-scf-largemem/n=128/aims.hugemem-20261101.n=128.out"
    return f"8x8x8/hse06-scf-largemem/n={n}/aims.scf.n={n}.out"


def path_8_hse_3322_dipole(n: int) -> str:
    if n == 128:
        return "8x8x8/hse06-dipole-production/n=128/aims.hugemem-20261101.n=128.out"
    return f"8x8x8/hse06-dipole-production/n={n}/aims.production.n={n}.out"


def path_8_hse_3211_dipole(n: int) -> str:
    if n == 128:
        return "8x8x8/dipole-grid-3-2-1-1/hse06/n=128/aims.hugemem-20261101.n=128.out"
    return f"8x8x8/dipole-grid-3-2-1-1/hse06/n={n}/aims.grid3211.n={n}.out"


SERIES = (
    {
        "series_id": "4x4x4_lda_p3644",
        "supercell": "4x4x4",
        "k_grid": "2 2 2",
        "functional": "LDA",
        "polarization_grid": "3 6 4 4",
        "cores": (128, 256, 512, 1024, 2048),
        "dipole": path_4_lda_3644_dipole,
        "scf": path_4_lda_scf,
        "resource_class": "normalmem",
        "method": "independent SCF and dipole allocations",
    },
    {
        "series_id": "4x4x4_hse06_p3644",
        "supercell": "4x4x4",
        "k_grid": "2 2 2",
        "functional": "HSE06",
        "polarization_grid": "3 6 4 4",
        "cores": (128, 256, 512, 1024, 2048),
        "dipole": path_4_hse_3644_dipole,
        "scf": path_4_hse_scf,
        "resource_class": "normalmem",
        "method": "independent SCF and dipole allocations",
    },
    {
        "series_id": "4x4x4_lda_p3422",
        "supercell": "4x4x4",
        "k_grid": "2 2 2",
        "functional": "LDA",
        "polarization_grid": "3 4 2 2",
        "cores": (128, 256, 512, 1024, 2048),
        "dipole": path_4_lda_3422_dipole,
        "scf": path_4_lda_scf,
        "resource_class": "normalmem",
        "method": "independent SCF and dipole allocations",
    },
    {
        "series_id": "4x4x4_hse06_p3422",
        "supercell": "4x4x4",
        "k_grid": "2 2 2",
        "functional": "HSE06",
        "polarization_grid": "3 4 2 2",
        "cores": (128, 256, 512, 1024, 2048),
        "dipole": path_4_hse_3422_paired_dipole,
        "scf": path_4_hse_3422_paired_scf,
        "resource_class": "normalmem",
        "method": "SCF and dipole sequentially coallocated on exclusive nodes",
    },
    {
        "series_id": "8x8x8_lda_p3322",
        "supercell": "8x8x8",
        "k_grid": "1 1 1",
        "functional": "LDA",
        "polarization_grid": "3 3 2 2",
        "cores": (128, 256, 512, 1024, 2048),
        "dipole": path_8_lda_3322_dipole,
        "scf": path_8_lda_scf,
        "resource_class": "largemem",
        "method": "independent SCF and dipole allocations",
    },
    {
        "series_id": "8x8x8_lda_p3211",
        "supercell": "8x8x8",
        "k_grid": "1 1 1",
        "functional": "LDA",
        "polarization_grid": "3 2 1 1",
        "cores": (128, 256, 512, 1024, 2048),
        "dipole": path_8_lda_3211_dipole,
        "scf": path_8_lda_scf,
        "resource_class": "largemem",
        "method": "independent SCF and dipole allocations",
    },
    {
        "series_id": "8x8x8_hse06_p3322",
        "supercell": "8x8x8",
        "k_grid": "1 1 1",
        "functional": "HSE06",
        "polarization_grid": "3 3 2 2",
        "cores": (128, 512, 1024, 2048),
        "dipole": path_8_hse_3322_dipole,
        "scf": path_8_hse_scf,
        "resource_class": "hugemem at 128; largemem otherwise",
        "method": "independent SCF and dipole allocations",
    },
    {
        "series_id": "8x8x8_hse06_p3211",
        "supercell": "8x8x8",
        "k_grid": "1 1 1",
        "functional": "HSE06",
        "polarization_grid": "3 2 1 1",
        "cores": (128, 512, 1024, 2048),
        "dipole": path_8_hse_3211_dipole,
        "scf": path_8_hse_scf,
        "resource_class": "hugemem at 128; largemem otherwise",
        "method": "independent SCF and dipole allocations",
    },
)


def main() -> None:
    timing_rows: list[dict] = []
    summary_rows: list[dict] = []
    manifest: dict[str, set[str]] = {}
    grid_order = {"3 6 4 4": 0, "3 4 2 2": 1, "3 3 2 2": 0, "3 2 1 1": 1}
    ordered_series = sorted(
        SERIES,
        key=lambda series: (
            int(series["supercell"].split("x")[0]),
            {"LDA": 0, "HSE06": 1}[series["functional"]],
            -grid_order[series["polarization_grid"]],
        ),
    )
    for series in ordered_series:
        rows = []
        memory_records = []
        for cores in series["cores"]:
            dipole_file = series["dipole"](cores)
            scf_file = series["scf"](cores)
            dipole_time = total_time(dipole_file)
            scf_time = total_time(scf_file)
            dipole_memory_mb = peak_tracked_memory_mb(dipole_file)
            scf_memory_mb = peak_tracked_memory_mb(scf_file)
            memory_records.extend(((dipole_memory_mb, cores, "dipole"), (scf_memory_mb, cores, "scf")))
            components = component_times(dipole_file)
            row = {
                "series_id": series["series_id"],
                "supercell": series["supercell"],
                "k_grid": series["k_grid"],
                "functional": series["functional"],
                "polarization_grid": series["polarization_grid"],
                "cores": cores,
                "resource_class": series["resource_class"],
                "method": series["method"],
                "dipole_time_s": f"{dipole_time:.3f}",
                "scf_time_s": f"{scf_time:.3f}",
                "polarization_time_s": f"{dipole_time - scf_time:.3f}",
                **{f"{field}_time_s": f"{value:.3f}" for field, value in components.items()},
                "extra_cost_s": f"{dipole_time - scf_time - sum(components.values()):.3f}",
                "dipole_peak_tracked_memory_mb_per_rank": f"{dipole_memory_mb:.3f}",
                "scf_peak_tracked_memory_mb_per_rank": f"{scf_memory_mb:.3f}",
                **{
                    f"{field}_raw_share_percent": f"{100.0 * value / sum(components.values()):.6f}"
                    for field, value in components.items()
                },
                "extra_cost_raw_share_percent": f"{100.0 * (dipole_time - scf_time - sum(components.values())) / sum(components.values()):.6f}",
                "dipole_raw_file": f"raw/{dipole_file}",
                "scf_raw_file": f"raw/{scf_file}",
            }
            timing_rows.append(row)
            rows.append(
                {
                    **row,
                    "polarization_time_s": dipole_time - scf_time,
                    **{f"{field}_time_s": value for field, value in components.items()},
                    "extra_cost_s": dipole_time - scf_time - sum(components.values()),
                    "extra_cost_magnitude_s": abs(dipole_time - scf_time - sum(components.values())),
                    "cores": cores,
                }
            )
            manifest.setdefault(f"raw/{dipole_file}", set()).add(series["series_id"])
            manifest.setdefault(f"raw/{scf_file}", set()).add(series["series_id"])
        alpha, total_intercept, r_squared = fit_power_law(rows)
        component_fits = {}
        component_models = {}
        for field in COMPONENTS:
            value_key = f"{field}_time_s"
            positive_rows = [row for row in rows if row[value_key] > 0.0]
            if len(positive_rows) >= 3:
                component_alpha, component_intercept, component_r_squared = fit_power_law(positive_rows, value_key)
                component_models[field] = (component_alpha, component_intercept)
                component_fits.update(
                    {
                        f"{field}_cores_used": " ".join(str(row["cores"]) for row in positive_rows),
                        f"{field}_scaling_power_p": f"{abs(component_alpha):.6f}",
                        f"{field}_r_squared": f"{component_r_squared:.6f}",
                    }
                )
            else:
                component_fits.update(
                    {
                        f"{field}_cores_used": " ".join(str(row["cores"]) for row in positive_rows),
                        f"{field}_scaling_power_p": "",
                        f"{field}_r_squared": "",
                    }
                )
        raw_share_ranges = {}
        for field in (*COMPONENTS, "extra_cost"):
            key = f"{field}_raw_share_percent"
            component_total = lambda row: sum(row[f"{component}_time_s"] for component in COMPONENTS)
            shares = [100.0 * row[f"{field}_time_s"] / component_total(row) for row in rows] if field in COMPONENTS else [100.0 * row["extra_cost_s"] / component_total(row) for row in rows]
            raw_share_ranges.update(
                {
                    f"{field}_raw_share_percent_min": f"{min(shares):.6f}",
                    f"{field}_raw_share_percent_max": f"{max(shares):.6f}",
                }
            )
        extra_rows = [row for row in rows if row["extra_cost_magnitude_s"] > 0.0]
        extra_alpha, extra_intercept, extra_r_squared = fit_power_law(extra_rows, "extra_cost_magnitude_s")
        contribution_models = {**component_models, "extra_cost_magnitude": (extra_alpha, extra_intercept)}
        fitted_share_ranges = {}
        for field, (contribution_alpha, contribution_intercept) in contribution_models.items():
            shares = [
                100.0 * math.exp(contribution_intercept) * cores**contribution_alpha
                / (math.exp(total_intercept) * cores**alpha)
                for cores in series["cores"]
            ]
            fitted_share_ranges.update(
                {
                    f"{field}_fitted_share_percent_min": f"{min(shares):.3f}",
                    f"{field}_fitted_share_percent_max": f"{max(shares):.3f}",
                }
            )
        max_memory_mb, max_memory_cores, max_memory_stage = max(memory_records)
        memory_partition = peak_memory_partition(series, max_memory_cores)
        memory_percent = 100.0 * max_memory_mb * 128.0 / PARTITION_MEMORY_MB[memory_partition]
        longest = max(rows, key=lambda row: float(row["dipole_time_s"]))
        summary_rows.append(
            {
                "series_id": series["series_id"],
                "supercell": series["supercell"],
                "k_grid": series["k_grid"],
                "functional": series["functional"],
                "polarization_grid": series["polarization_grid"],
                "cores_used": " ".join(str(core) for core in series["cores"]),
                "n_points": len(rows),
                "scaling_power_p": f"{abs(alpha):.6f}",
                "r_squared": f"{r_squared:.6f}",
                "longest_stage": "dipole",
                "longest_cores": longest["cores"],
                "longest_time_s": longest["dipole_time_s"],
                "longest_time_hms": hms(float(longest["dipole_time_s"])),
                "resource_class": series["resource_class"],
                "method": series["method"],
                "max_tracked_memory_mb_per_rank": f"{max_memory_mb:.3f}",
                "max_tracked_memory_gib_per_rank": f"{max_memory_mb / 1024.0:.3f}",
                "max_tracked_memory_gib_per_node_upper_bound": f"{max_memory_mb * 128.0 / 1024.0:.3f}",
                "max_tracked_memory_partition": memory_partition,
                "max_tracked_memory_partition_percent": f"{memory_percent:.3f}",
                "max_tracked_memory_cores": max_memory_cores,
                "max_tracked_memory_stage": max_memory_stage,
                "nodes_partition_summary": nodes_partition_summary(series),
                "extra_cost_magnitude_cores_used": " ".join(str(row["cores"]) for row in extra_rows),
                "extra_cost_magnitude_scaling_power_p": f"{abs(extra_alpha):.6f}",
                "extra_cost_magnitude_r_squared": f"{extra_r_squared:.6f}",
                **component_fits,
                **fitted_share_ranges,
                **raw_share_ranges,
            }
        )

    with (ROOT / "timing_data.csv").open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(timing_rows[0]))
        writer.writeheader()
        writer.writerows(timing_rows)
    with (ROOT / "scaling_summary.csv").open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(summary_rows[0]))
        writer.writeheader()
        writer.writerows(summary_rows)
    with (ROOT / "raw_files_manifest.csv").open("w", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(("raw_file", "used_by_series"))
        for raw_file in sorted(manifest):
            writer.writerow((raw_file, "; ".join(sorted(manifest[raw_file]))))


if __name__ == "__main__":
    main()
