#!/usr/bin/env python3
"""Collect and tabulate HSE06/revPBE0 FHI-aims output files.

Run with --collect once to copy matching output files from the two source
projects into this directory.  Run without arguments afterwards to regenerate
the CSV from the copied output files and the accompanying manifest.
"""

from __future__ import annotations

import argparse
import csv
import re
import shutil
from pathlib import Path


SOURCE_ROOTS = {
    "water": Path("/viper/u1/elsto/works/ScaLAPACK-performance/water"),
    "BaTiO3": Path("/viper/u1/elsto/works/ScaLAPACK-performance/BaTiO3"),
}

XC_RE = re.compile(r"^\s*xc\s+(hse06|revpbe0)\b", re.I | re.M)
ATOM_RE = re.compile(r"Number of atoms\s*:\s*(\d+)", re.I)
RANKS_RE = re.compile(r"Integration load balanced across\s*(\d+)\s+MPI tasks", re.I)
BASIS_RE = re.compile(r"Total number of basis functions\s*:\s*(\d+)", re.I)
MAX_BASIS_RE = re.compile(r"Maximum number of basis functions\s*:\s*(\d+)", re.I)
FOCK_RE = re.compile(
    r"Assumed free memory per node for Fock matrix prefactors \[GB\]\s+([0-9.]+)",
    re.I,
)
COULOMB_RE = re.compile(
    r"Memory per instance for Coulomb / ovlp matrix \[GB\]\s+([0-9.]+)\s+([0-9.]+)",
    re.I,
)
NODES_RE = re.compile(r"Number of nodes, tasks per node\s+(\d+)\s+(\d+)", re.I)
INSTANCES_RE = re.compile(r"Number of instances:\s*(\d+)", re.I)
HOST_RE = re.compile(r"^\s*Task\s+\d+\s+on host\s+(\S+)\s+reporting\.", re.I | re.M)
JOB_RE = re.compile(r"(?:StepId=|job_)(\d+)", re.I)
TIME_RE = re.compile(r"\[([0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9:.+-]+)\]\s+error:", re.I)
OOM_RE = re.compile(
    r"out of memory|oom[_ -]kill|cannot allocate memory|std::bad_alloc|bad_alloc|malloc.*fail|allocation.*fail",
    re.I,
)
ERROR_RE = re.compile(
    r"\*\*\* STEP .*?(?:CANCELLED|FAILED)|srun: error:|forrtl: error|segmentation fault|SIG(?:SEGV|ABRT|KILL)|FATAL|ERROR",
    re.I,
)
PHASE_RULES = [
    (re.compile(r"Transferring Coulomb matrix to final data layout", re.I), "Coulomb matrix layout transfer"),
    (re.compile(r"--- Calculating Coulomb matrices", re.I), "Coulomb matrix construction"),
    (re.compile(r"--- Calculating OVLP3FN", re.I), "OVLP3FN construction"),
    (re.compile(r"Number of atoms pairs in BvK cells", re.I), "Fock/Coulomb setup: BvK atom-pair construction"),
    (re.compile(r"Calculating non-local Hartree-Fock exchange|Exact exchange progress report", re.I), "Fock matrix construction"),
    (re.compile(r"Evaluating density matrix", re.I), "SCF density-matrix evaluation"),
    (re.compile(r"Integrating Hamiltonian matrix", re.I), "SCF Hamiltonian integration"),
    (re.compile(r"Calculating k-points", re.I), "post-SCF dipole k-point processing"),
    (re.compile(r"Begin self-consistency", re.I), "SCF initialization"),
]

MANIFEST_FIELDS = [
    "bundle_filepath",
    "source_filepath",
    "partition",
    "constraint",
    "resource_metadata_source",
]
DATAFRAME_FIELDS = [
    "system",
    "functional",
    "filepath",
    "bundle_filepath",
    "status",
    "number_of_atoms",
    "number_of_basis_functions",
    "maximum_number_of_basis_functions",
    "number_of_ranks",
    "partition",
    "constraint",
    "resource_metadata_source",
    "failure_phase",
    "last_phase_marker",
    "failure_timestamp",
    "job_id",
    "fock_prefactor_free_memory_per_node_gb",
    "coulomb_memory_per_instance_gb",
    "ovlp_memory_per_instance_gb",
    "number_of_nodes",
    "tasks_per_node",
    "number_of_instances",
    "allocated_node_hostnames",
    "detected_number_of_nodes",
    "available_memory_per_node_mb",
    "available_memory_per_node_gb",
    "node_cpus",
    "node_features",
]


def first(pattern: re.Pattern[str], text: str, group: int = 1) -> str | None:
    match = pattern.search(text)
    return match.group(group) if match else None


def output_rank(path: Path) -> int | None:
    for item in (path.name, *(parent.name for parent in path.parents)):
        match = re.search(r"(?:aims\.n=|aims\.|n=)(\d+)(?:\D|$)", item)
        if match:
            return int(match.group(1))
    return None


def load_node_inventory(dataset_dir: Path) -> dict[str, dict[str, str]]:
    """Load node capacities keyed by normalized hostname, if supplied."""
    inventory_path = dataset_dir / "general_nodes.csv"
    if not inventory_path.exists():
        return {}
    with inventory_path.open(newline="") as handle:
        return {
            row["hostname"].lower(): row
            for row in csv.DictReader(handle)
            if row.get("hostname")
        }


def formatted_memory_gb(memory_mb: str) -> str:
    """Convert the inventory's decimal MB capacity to decimal GB."""
    try:
        return f"{float(memory_mb) / 1000:g}"
    except (TypeError, ValueError):
        return ""


def node_metadata(text: str, inventory: dict[str, dict[str, str]]) -> dict[str, str]:
    """Extract output hostnames and join them to the node inventory.

    A job can theoretically span heterogeneous nodes.  Per-node fields are
    therefore pipe-delimited sets of distinct values instead of assuming that
    every host has the same hardware.
    """
    hostnames = sorted({match.group(1).lower() for match in HOST_RE.finditer(text)})
    node_records = [inventory[hostname] for hostname in hostnames if hostname in inventory]

    def distinct(field: str) -> str:
        values = {record.get(field, "") for record in node_records if record.get(field, "")}
        if field in {"cpus", "total_memory_mb"}:
            return "|".join(sorted(values, key=float))
        return "|".join(sorted(values))

    memory_mb = distinct("total_memory_mb")
    return {
        "allocated_node_hostnames": ";".join(hostnames),
        "detected_number_of_nodes": str(len(hostnames)) if hostnames else "",
        "available_memory_per_node_mb": memory_mb,
        "available_memory_per_node_gb": "|".join(
            formatted_memory_gb(value) for value in memory_mb.split("|") if value
        ),
        "node_cpus": distinct("cpus"),
        "node_features": distinct("features"),
    }


def resource_metadata(path: Path, root: Path) -> tuple[str, str, str]:
    """Find Slurm settings from a nearby submission or runner script."""
    partition = constraint = source = None
    current = path.parent
    while True:
        for script in current.glob("*.sh"):
            try:
                script_text = script.read_text(errors="replace")
            except OSError:
                continue
            if partition is None:
                match = re.search(r"--partition(?:=|\s+)\"?([A-Za-z0-9_-]+)", script_text)
                if match:
                    partition, source = match.group(1), str(script)
            if constraint is None:
                match = re.search(r"--constraint(?:=|\s+)\"?([A-Za-z0-9_,-]+)", script_text)
                if match:
                    constraint, source = match.group(1), str(script)
        if (partition and constraint) or current == root or current.parent == current:
            break
        current = current.parent
    lowered = str(path).lower()
    if constraint is None:
        for known_constraint in ("hugemem", "largemem"):
            if known_constraint in lowered:
                constraint = known_constraint
                source = "inferred from campaign path"
                break
    return partition or "unknown", constraint or "unknown", source or "not found"


def classify_failure(text: str, success: bool) -> tuple[str, str, str, str]:
    if success:
        return "succeeded", "", "", ""
    terminal = OOM_RE.search(text) or ERROR_RE.search(text)
    if not terminal:
        return "incomplete_or_unknown", "", "", ""
    boundary = terminal.start()
    preceding = text[:boundary]
    latest = None
    label = "phase not identified"
    for pattern, candidate_label in PHASE_RULES:
        for match in pattern.finditer(preceding):
            if latest is None or match.start() > latest.start():
                latest, label = match, candidate_label
    marker = ""
    if latest:
        marker_end = preceding.find("\n", latest.start())
        marker = preceding[latest.start() : marker_end if marker_end != -1 else len(preceding)].strip()
    nearby = text[max(0, boundary - 500) : boundary + 500]
    timestamp = first(TIME_RE, nearby) or ""
    return ("failed_oom" if OOM_RE.search(text) else "failed"), label, marker, timestamp


def is_aims_output(path: Path) -> bool:
    return path.name.lstrip("~").startswith("aims") and path.suffix == ".out"


def collect(dataset_dir: Path) -> None:
    outputs_dir = dataset_dir / "outputs"
    manifest_rows: list[dict[str, str]] = []
    for system, root in SOURCE_ROOTS.items():
        for source_path in sorted(root.rglob("*.out")):
            # Exclude the dataset itself when it is nested under BaTiO3.
            try:
                source_path.relative_to(dataset_dir)
                continue
            except ValueError:
                pass
            if not is_aims_output(source_path):
                continue
            try:
                text = source_path.read_text(errors="replace")
            except OSError:
                continue
            if not XC_RE.search(text):
                continue
            bundle_path = outputs_dir / system / source_path.relative_to(root)
            bundle_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source_path, bundle_path)
            partition, constraint, resource_source = resource_metadata(source_path, root)
            manifest_rows.append(
                {
                    "bundle_filepath": str(bundle_path.relative_to(dataset_dir)),
                    "source_filepath": str(source_path),
                    "partition": partition,
                    "constraint": constraint,
                    "resource_metadata_source": resource_source,
                }
            )
    with (dataset_dir / "source_manifest.csv").open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=MANIFEST_FIELDS)
        writer.writeheader()
        writer.writerows(manifest_rows)
    print(f"Collected {len(manifest_rows)} FHI-aims HSE06/revPBE0 outputs.")


def load_manifest(dataset_dir: Path) -> dict[str, dict[str, str]]:
    manifest = dataset_dir / "source_manifest.csv"
    if not manifest.exists():
        return {}
    with manifest.open(newline="") as handle:
        return {row["bundle_filepath"]: row for row in csv.DictReader(handle)}


def build_dataframe(dataset_dir: Path) -> int:
    manifest = load_manifest(dataset_dir)
    node_inventory = load_node_inventory(dataset_dir)
    rows: list[dict[str, str | int]] = []
    outputs_dir = dataset_dir / "outputs"
    for path in sorted(outputs_dir.rglob("*.out")):
        if not is_aims_output(path):
            continue
        try:
            text = path.read_text(errors="replace")
        except OSError:
            continue
        xc = XC_RE.search(text)
        if not xc:
            continue
        functional = "HSE06" if xc.group(1).lower() == "hse06" else "revPBE0"
        system = path.relative_to(outputs_dir).parts[0]
        bundle_filepath = str(path.relative_to(dataset_dir))
        source = manifest.get(bundle_filepath, {})
        success = "Have a nice day." in text
        status, failure_phase, marker, failure_timestamp = classify_failure(text, success)
        ranks = first(RANKS_RE, text) or output_rank(path) or ""
        nodes = node_metadata(text, node_inventory)
        rows.append(
            {
                "system": system,
                "functional": functional,
                "filepath": source.get("source_filepath", bundle_filepath),
                "bundle_filepath": bundle_filepath,
                "status": status,
                "number_of_atoms": first(ATOM_RE, text) or "",
                "number_of_basis_functions": first(BASIS_RE, text) or "",
                "maximum_number_of_basis_functions": first(MAX_BASIS_RE, text) or "",
                "number_of_ranks": ranks,
                "partition": source.get("partition", "unknown"),
                "constraint": source.get("constraint", "unknown"),
                "resource_metadata_source": source.get("resource_metadata_source", "not found"),
                "failure_phase": failure_phase,
                "last_phase_marker": marker,
                "failure_timestamp": failure_timestamp,
                "job_id": first(JOB_RE, text) or "",
                "fock_prefactor_free_memory_per_node_gb": first(FOCK_RE, text) or "",
                "coulomb_memory_per_instance_gb": first(COULOMB_RE, text, 1) or "",
                "ovlp_memory_per_instance_gb": first(COULOMB_RE, text, 2) or "",
                "number_of_nodes": first(NODES_RE, text, 1) or "",
                "tasks_per_node": first(NODES_RE, text, 2) or "",
                "number_of_instances": first(INSTANCES_RE, text) or "",
                **nodes,
            }
        )
    with (dataset_dir / "fhi_aims_hse06_revpbe0_calculations.csv").open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=DATAFRAME_FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    print(f"Wrote {len(rows)} rows to fhi_aims_hse06_revpbe0_calculations.csv")
    return len(rows)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--collect", action="store_true", help="copy source outputs and refresh the manifest")
    args = parser.parse_args()
    dataset_dir = Path(__file__).resolve().parent
    if args.collect:
        collect(dataset_dir)
    build_dataframe(dataset_dir)


if __name__ == "__main__":
    main()
