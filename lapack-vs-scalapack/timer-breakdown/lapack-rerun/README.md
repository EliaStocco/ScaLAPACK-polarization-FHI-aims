# LAPACK rerun with the newly built FHI-aims executable

This directory stages independent reruns of every previously completed LAPACK
case: 8, 16, 32, 64, 128, 256, 512, and 1024 MPI ranks. Each case receives separate inputs, output, and Slurm logs.

The executable is `../FHI-aims/build/aims.260527.scalapack.mpi.x` (SHA-256
`892f5f55b044479e44756a978d17e24e9030351f8a3d5f3e9b41a56606b2567a`). CSC
restart inputs are symlinks to `../../converge` and are never removed or
modified. The 45-minute time limit covers the prior maximum measured elapsed
time of about 28 minutes.
