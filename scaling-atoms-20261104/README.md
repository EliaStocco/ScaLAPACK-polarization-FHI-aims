# Updated atom-scaling plot (2026-11-04)

This directory is self-contained and regenerates the atom-scaling comparison
with the old LAPACK data (blue) and the 4 November 2026 ScaLAPACK rerun data
(orange).

`lapack/` contains the old LAPACK SCF and dipole `aims.out` pairs.  The
ScaLAPACK rerun SCF and dipole outputs are preserved unchanged in
`scalapack-rerun-20261104-outputs.zip`; they cover supercells from `2x2x2`
(16 atoms) through `8x8x8` (1024 atoms), all at 512 MPI ranks.
The preserved `1x1x1` LAPACK pair is automatically excluded because its
dipole-minus-SCF time is negative, as in the original scaling workflow.

The old and rerun Slurm records both report 4 nodes, 512 MPI tasks, and 1024
allocated CPUs.  They are therefore matched at the allocation level.  The
main runtime difference visible in the outputs is the FHI-aims build: the old
files report version `260527`, while the rerun files report version `261007`.
The node lists also differ: the old jobs used `vipc` nodes, whereas several
rerun jobs used `vipl` (and one used `vipm`) nodes.  The archive does not
contain the rerun submission script or hardware specifications, so the
relative contributions of the newer build and node type cannot be separated
from these files alone.

Run the complete reproducible workflow from this directory:

```bash
./run.sh
```

This writes `dataframe.csv` and `scaling-atoms-20261104.pdf`.  `extract.py`
parses raw FHI-aims output directly; `plot.py` uses the local style and local
structure-image assets.  The only runtime Python requirements are NumPy and
Matplotlib (and a LaTeX installation if using the supplied plotting style).
