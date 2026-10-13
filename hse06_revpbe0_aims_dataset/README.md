# FHI-aims HSE06/revPBE0 dataset

This folder is a self-contained analysis bundle for FHI-aims calculations on
water and BaTiO3.  It collects HSE06 and revPBE0 output files, extracts
calculation, failure, memory, allocation, and node-hardware metadata into one
CSV table, and provides a notebook for exploratory analysis.

## Contents

| Path | Purpose |
| --- | --- |
| `outputs/` | Bundled FHI-aims `.out` files, grouped by system and original campaign path. |
| `build_dataframe.py` | Rebuilds the tabular dataset by parsing every bundled output. |
| `fhi_aims_hse06_revpbe0_calculations.csv` | Generated dataframe; one row per bundled output file. |
| `source_manifest.csv` | Maps each bundled output to its original source path and Slurm metadata. |
| `general_nodes.csv` | Snapshot of node hostname, CPU count, total memory, features, partition, and state. |
| `analyse_failures_by_instances.ipynb` | Failure-rate and resource-allocation analysis notebook. |
| `plots/` | PNGs written by the notebook plotting cells. |

## Rebuild the dataframe

Run this from this directory after changing `build_dataframe.py`, adding output
files, or replacing `general_nodes.csv`:

```bash
python3 build_dataframe.py
```

The command scans `outputs/**/*.out` and overwrites
`fhi_aims_hse06_revpbe0_calculations.csv`.

`python3 build_dataframe.py --collect` also attempts to copy matching outputs
from the source-project locations hard-coded in `SOURCE_ROOTS`.  That command
is only usable on a machine where those source paths are available.

## Extracted data

The generated CSV includes:

- Calculation identity: system, functional, source/bundled path, atom count,
  regular and maximum basis-function counts, MPI ranks, and job ID. The
  maximum count is the extended-basis leading dimension reported in FHI-aims'
  structure-dependent array-size summary.
- Outcome information: success/failure status, suspected failure phase, marker,
  and timestamp.  OOM failures are identified from common scheduler and
  allocation error messages.
- Fock/Coulomb allocation data printed by FHI-aims: free memory for Fock
  prefactors, Coulomb and OVLP memory per instance, nodes, tasks per node, and
  number of instances.
- Host allocation data parsed from `Task ... on host ... reporting.` lines:
  `allocated_node_hostnames` and `detected_number_of_nodes`.
- Hardware data joined from `general_nodes.csv`: per-node memory in MB and GB,
  CPU count, and node features.

The `available_memory_per_node_*` columns are derived from the inventory's
`total_memory_mb` field. They describe node capacity, not the runtime free
memory. Use `fock_prefactor_free_memory_per_node_gb` for FHI-aims' own runtime
free-memory estimate.

If a run spans heterogeneous nodes, the per-node hardware columns contain
pipe-separated distinct values; this avoids silently assigning one node's
capacity to the whole allocation.

## Analysis notebook

`analyse_failures_by_instances.ipynb` investigates whether failures correlate
with `number_of_instances`, then stratifies by system, functional, atom count,
and allocation. It also compares water calculations with 588 atoms between
HSE06 and revPBE0, and plots maximum basis dimension versus total MPI tasks.
That plot colors each run by available node-memory capacity and uses circles
and X markers for successful and failed jobs, respectively.

Plots use `../style.mplstyle` and are saved under `plots/` when cells run. The
notebook needs NumPy, Matplotlib, and SciPy for its main analysis; the optional
adjusted regression additionally needs pandas and statsmodels.

## Important caveats

- A row is an output file, not necessarily an independent calculation. Some
  files are copied into `results/` or backups and can be byte-identical. Hash
  outputs before calculating independent-run statistics.
- Failed jobs can terminate before emitting Fock allocation lines. Analyses
  requiring instance or node metadata may therefore exclude a non-random subset
  of failures.
- Hardware metadata come from a node-inventory snapshot. They should be treated
  as allocation capacity metadata, not a historical measurement of free memory
  at job start.
- The raw FHI-aims `load_balancing` setting is not yet a dataframe column.
  Outputs can be inspected directly for `load_balancing .true.` or `.false.`;
  an omitted setting should not be assumed to mean an explicit false setting.
