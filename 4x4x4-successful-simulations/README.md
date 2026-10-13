# Successful 4x4x4 BaTiO3 simulations

This archive contains the cleanly completed 4x4x4 FHI-aims scaling runs from
the HSE06/LDA water-executable campaign.  It preserves the original directory
layout so that each result can be related directly to its calculation type,
functional, and MPI rank count.

## Included calculations

| Calculation | Functional | Completed rank counts |
| --- | --- | --- |
| SCF | LDA | 128, 256, 512, 768, 900, 1024, 1080, 2048 |
| Dipole | LDA | 128, 256, 512, 768, 900, 1023, 1080, 2048 |
| SCF | HSE06 | 256, 512, 768, 900, 1024, 1080, 2048 |
| Dipole | HSE06 | 256, 512, 768, 900, 1023, 1080, 2048 |

The two excluded calculations are `scf-HSE06/n=128` and
`dipole-HSE06/n=128`.  They ended in out-of-memory failures and are therefore
not suitable for analysis as completed calculations.

## Layout

```
4x4x4/
  scf-LDA/       # SCF runs using LDA
  dipole-LDA/    # dipole/Wannier-centre runs using LDA
  scf-HSE06/     # SCF runs using HSE06
  dipole-HSE06/  # dipole/Wannier-centre runs using HSE06
    control.in       # shared FHI-aims settings for that calculation family
    geometry.in      # structure
    n=<ranks>/       # one completed calculation at a given MPI rank count
      aims.n=<ranks>.out  # primary FHI-aims output
      slurm-<jobid>.out   # Slurm standard output
      slurm-<jobid>.err   # Slurm standard error
      job.log             # start/end timestamps
scripts/
  run_aims.sh
  submit_all.sh
```

## Suggested analysis workflow

1. Select a calculation family, for example
   `4x4x4/dipole-HSE06/n=1024/`.
2. Read `job.log` for the run duration boundaries and `aims.n=1024.out` for
   FHI-aims timing, convergence, and physical results.
3. Use the `slurm-*.out`/`.err` files to diagnose scheduler-level details.
4. Compare equivalent `n=<ranks>` directories only within the same
   calculation family and functional.

Every included `aims.n=*.out` file has a clean FHI-aims termination marker
(`Have a nice day.` or `Leaving FHI-aims.`).

## Timing plot

Run either analysis from any directory with:

```bash
python3 4x4x4-successful-simulations/plot_power_law.py
python3 4x4x4-successful-simulations/plot_double_power_law.py
```

This extracts the final FHI-aims `max(cpu_time)` values and plots the
polarization overhead (`dipole - SCF`) for LDA and HSE06. The scripts share
`analysis-dataframe.csv` but write separate fit and plot files:

- `fit-power-law.json` and `BaTiO3.4x4x4.power-law.pdf`
- `fit-double-power-law.json` and `BaTiO3.4x4x4.double-power-law.pdf`

Both fits exclude the 2048-core points, which remain in the CSV and plots.
The LDA fit uses 128, 256, 512, and 1080 cores; HSE06 uses 256, 512, and 1080
cores because it has no successful 128-core result. The single-power-law model is
`time = A * ncores**m`. The double-power-law model is
`time = A * ncores**m + B * ncores**n` and uses positive prefactors and
non-positive exponents. The HSE06 double-power-law fit remains underdetermined
because it has only three fitted points for four parameters.

The 768- and 900-rank results and the 1023-rank dipole/1024-rank SCF results
are excluded from both the extracted CSV and the plots.
