# Lattice and internal-site parameters (Tables S1–S4)

The "this work" entries of Tables S1–S4 are computed from the relaxed
geometries `validation/<system>/<phase>/<xc>/lapack/geometry.in` with the
fd2bec command-line tools (<https://github.com/EliaStocco/fd2bec>).

Regenerate everything with

```bash
bash run.sh
```

## Steps and outputs

1. `prepare.py` moves the A-site atom (Ba, Pb or Bi) to the top of each
   geometry, so that it is placed at the origin as in Table S5, and writes
   `geometries/<system>_<phase>_<xc>.in`, `geometries/all.extxyz` and
   `geometries/names.txt`.
2. `space_group_dataset` writes `lattice.csv` (a, b, c, α, β, γ and space
   group); its rows follow the order of `geometries/names.txt`.
   The log is `space_group_dataset.log`.
3. `tensor_symmetries -n positions` writes `positions/<name>.txt` for each
   non-cubic structure.
   Each file shows the symmetry-allowed fractional positions in terms of the
   parameters `a`, `b`, … and their values in the block
   "Symmetry-inequivalent component values".
   Cubic structures have no free internal parameters and are skipped.

## From fd2bec parameters to table columns

| Table | Structure | Table column | fd2bec parameter |
| --- | --- | --- | --- |
| S1 | BaTiO3 cubic, tetragonal | a, c/a | `lattice.csv`: a, c/a |
| S1 | BaTiO3 tetragonal | dz_Ti, dz_O⊥, dz_O∥ | a, c, b |
| S2 | BaTiO3 rhombohedral | a, α | `lattice.csv`: a, alpha |
| S2 | BaTiO3 rhombohedral | Δr_Ti, Δr_O1, Δr_O2 | a, b, c |
| S3 | BiFeO3 R-3c, R3c | a, α | `lattice.csv`: a, alpha |
| S3 | BiFeO3 R-3c | x_Fe, x_O, y_O = z_O | 0.25 (fixed), 0, a |
| S3 | BiFeO3 R3c | x_Fe, x_O, y_O, z_O | a, b, c, d |
| S4 | PbTiO3 cubic, tetragonal (`displaced`) | a, c/a | `lattice.csv`: a, c/a |
| S4 | PbTiO3 tetragonal (`displaced`) | dz_Ti, dz_O⊥, dz_O∥ | a, b, c |

fd2bec reports the PbTiO3 positions in the domain where all displacements are
along −z; Table S5 uses the equivalent domain along +z, so the parameters have
the same values.
