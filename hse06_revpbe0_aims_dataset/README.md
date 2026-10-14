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
  regular and maximum basis-function counts, nominal k-grid-point count, MPI
  ranks, and job ID. The
  maximum count is the extended-basis leading dimension reported in FHI-aims'
  structure-dependent array-size summary.
- Outcome information: success/failure status, suspected failure phase, marker,
  and timestamp.  OOM failures are identified from common scheduler and
  allocation error messages.
- Fock/Coulomb allocation data printed by FHI-aims: free memory for Fock
  prefactors, Coulomb and OVLP memory per instance, nodes, tasks per node, and
  number of instances.
- Fock auto-tuner diagnostics printed after Fock initialization: peak
  Hartree-Fock memory per node, selected Fock block size, residual free memory
  per node, and the number of atom pairs in Born-von Karman (BvK) cells.
- Exact-exchange configuration echoed from `control.in`: `load_balancing` and
  `use_alltoall`, plus `effective_load_balancing` and an evidence field parsed
  from runtime messages. `unset` retains the absence of a control-file echo.
  In every FHI-aims version present here, both options default to `false`.
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

The notebook also writes `plots/water_configuration_failure_map.png`, an
interpretable two-dimensional map of the effective `load_balancing` state and
the raw `use_alltoall` control-file echo for the 384- and 588-atom water runs.
It removes byte-identical copied outputs. The FHI-aims source establishes that
an omitted `use_alltoall` is effective `false`, so the apparent difference
between its omitted and explicit-false forms is a campaign/input-history
marker, not an all-to-all setting effect. The remaining load-balancing
association is observational; use matched reruns that change one setting at a
time to test it.

`plots/water_mpi_tasks_vs_node_memory_failure_map.png` is a second,
configuration-independent map: it plots total MPI tasks against allocated
node-memory capacity for the 384- and 588-atom water jobs. This pair was the
strongest numerical two-variable screen after excluding `use_alltoall` and
`load_balancing`, but its overlapping outcome cells show that resources alone
do not explain every failure.

`plots/all_systems_basis_kpoints_vs_memory_per_task_failure_map.png` places
all CSV rows, including BaTiO3, in one size/resource panel. Its x-axis is
maximum basis functions times the nominal k-grid-point count; its y-axis is
available node memory divided by the actual MPI tasks per node. Outcome is
encoded by colour and system/atom count by marker shape.

`plots/fock_memory_pressure_vs_matrix_work_failure_map.png` is a Fock-stage
diagnostic. It compares FHI-aims' reported free Fock memory against an
estimated per-node Coulomb/OVLP matrix allocation, and plots that fraction
against a dense-matrix workload-per-rank proxy. It deliberately excludes jobs
that ended before printing the Fock-memory report, so it is a diagnostic of
reached Fock stages rather than a complete failure-rate plot.

`plots/coulomb_memory_vs_matrix_work_failure_map.png` retains the same
dense-matrix-work-per-rank abscissa but uses FHI-aims' Coulomb-matrix memory
per instance as its ordinate. It is the strongest single alternate
reported-memory ordinate in the water-only screen, although it still has
substantial outcome overlap.

`plots/paper_guided_fock_work_vs_memory_pressure.png` follows the FHI-aims
hybrid-functional paper more directly. Its x-axis approximates the Fock-block
work assigned to an instance: BvK atom pairs times
`maximum_basis_functions / Fock_block_size / number_of_instances`. Its upper
row is the printed peak Hartree-Fock memory per node divided by the printed free
memory per node after Fock initialization; its lower row is their signed
difference (estimated headroom in GB). The difference is more directly
interpretable, while the ratio normalizes capacity across nodes. It is only
defined for jobs that reached that initialization stage, and therefore cannot
diagnose earlier failures. Circle versus cross encodes success versus failure
and colour encodes the system, atom count, and XC functional. Panels separate
the FHI-aims build.
This exposes that the water HSE06 failures in the mixed region occur in build
260824; the corresponding 260527 water HSE06 points are successful. It is a
strong campaign/build association, not proof that the build alone caused the
failure.

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
- The raw `load_balancing` and `use_alltoall` columns record only explicit
  control-file echoes. `effective_load_balancing` is the state inferred from
  the output runtime messages, accounting for late disabling when ScaLAPACK is
  unavailable. The bundled jobs use FHI-aims versions 251119, 260527, and
  260824; their `runtime_choices.f90` sets both options to `false` by default.
- `Integration load balanced across ...` is the ordinary initial spatial batch
  distribution and appears regardless of `use_load_balancing`. Do not use it
  to infer the option. `Using load balancing for integrations.` and
  `Start compute_balanced_batch_distribution` are the reliable positive
  runtime markers.
