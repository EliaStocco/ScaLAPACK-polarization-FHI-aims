# Unit-cell Born-effective-charge polarization-grid convergence

This calculation uses the supplied five-atom BaTiO3 unit cell. The SCF mesh is
fixed at `8 8 8`, while the Berry-phase polarization-string length is scanned
over `16, 20, 24, 28, 32, 36, 40, 48, 56, 64, 80`. The other two dimensions of
each direction-specific polarization mesh remain fixed at 8.

The symmetry-reduced finite-displacement geometries are stored once in
`geometries/`; each `k-grid-<n>/geometries` is a relative symbolic link to that
folder. Every grid retains an independent `results/` folder.

## Workflow

1. Activate fd2bec and prepare all finite-displacement inputs:

   ```bash
   source /u/elsto/venv/fd2bec/bin/activate
   ./prepare.sh
   ./prepare_density.sh
   ```

2. Submit the common reference-density job and all dependent grid jobs:

   ```bash
   ./submit_convergence.sh
   ```

   The density job writes the converged `8 8 8` ELSI CSC matrices. Each BEC
   job reuses those matrices for all displaced structures. Alternatively,
   submit `run_density.slurm`, wait for it to complete, and then submit
   `main.sh` to run all grids sequentially in one allocation.

3. Once calculations are complete, post-process and analyse them with fd2bec
   still active. From the parent `raw/` directory run:

   ```bash
   ./post_process_bec.sh
   python3 bec_kgrid_convergence/analyse_bec_convergence.py
   python3 plot_combined_convergence.py
   ```

   The post-processing step discovers every `raw/bec_*/k-grid-*` calculation
   with a `DONE` marker and writes its fd2bec `postprocess/bec.txt`. The BEC
   analysis uses the largest completed grid as its default reference and writes
   its CSV table and plot under `bec-convergence/`. The combined plot expects
   the direct-polarization table produced by
   `plot_polarization_convergence.py`.

The scanned values are defined in `prepare.sh`. Preparation does not submit any
jobs.
