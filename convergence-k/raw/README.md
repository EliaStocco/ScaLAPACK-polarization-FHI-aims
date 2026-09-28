# Unit-cell polarization-grid convergence

This directory contains two convergence tests for the supplied five-atom
BaTiO3 unit cell:

- the top-level `converge.sh` scans the Berry-phase polarization grid for the
  undisplaced structure;
- `bec_kgrid_convergence/` scans the same quantity for finite-displacement
  Born-effective-charge calculations.

Both workflows keep the SCF k-grid fixed at `8 8 8`. The polarization-string
length is scanned over `16, 20, 24, 28, 32, 36, 40, 48, 56, 64, 80`; the two
transverse grid dimensions remain fixed at 8. These values cover approximately
the same reciprocal-space resolution as the 2x2x2 tests while extending to the
80-point setting in the supplied unit-cell `control.in`.

## Direct polarization scan

Submit the scan from this directory:

```bash
sbatch converge.sh
```

The job first creates one converged `8 8 8` density matrix if no CSC restart
files are present, then runs each polarization grid using that restart. Existing
completed `results/aims.n=<n>.out` files are retained, so a timed-out job can be
resubmitted safely.

After the calculations finish:

```bash
python update_polarization_kgrid_csv.py
python plot_polarization_convergence.py
```

## BEC scan

Activate the fd2bec environment and follow
`bec_kgrid_convergence/README.md`. Once the calculations finish, create the
Born charges and all convergence figures from `raw/`:

```bash
./post_process_bec.sh
python bec_kgrid_convergence/analyse_bec_convergence.py
python plot_combined_convergence.py
```

`plot_polarization_convergence.py` writes the direct-polarization convergence
table and figure. The Born-charge analysis writes an analogous table and
figure, and `plot_combined_convergence.py` places the two errors in one panel
with a shared k-grid x-axis and separate y-axes.
