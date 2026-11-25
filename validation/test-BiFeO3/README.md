# BiFeO3 polarization-branch path

This directory contains the continuous BiFeO3 R-3c -> R3c distortion path used to determine the physically continuous polarization branch.
It is the reference workflow for interpreting the BiFeO3 polarization difference in Table 1 of the manuscript.

## Where to look

For the reported PBEsol result, read `summary.txt` first.
It gives the branch-unwrapped direct-lattice components at the two endpoints, their difference, the reconstructed Cartesian polarization difference, and its magnitude:

```text
Delta P1 = 0.404228621 C/m^2
Delta P2 = 0.404217984 C/m^2
Delta P3 = 0.404221137 C/m^2
|Delta P| = 1.003442667 C/m^2
```

These values round to the PBEsol `0.404` and `1.003` entries in Table 1.
The three nearly equal component differences arise from rhombohedral symmetry.

The primary calculation data are the ten FHI-aims outputs in `PBEsol/results/aims.n=0.out` through `PBEsol/results/aims.n=9.out`.
`n=0` is the centrosymmetric reference endpoint and `n=9` is the polar endpoint; the intermediate structures establish the continuous polarization branch.

## Derived files

`extract_folded_polarization.py` reads the raw FHI-aims outputs, follows the continuous branch, and writes:

- `folded_polarization.csv`, the complete per-structure data;
- `summary.txt`, the endpoint comparison quoted above.

The CSV is a derived record, not the starting point for checking the reported value.
When verifying the result, use `summary.txt`, then inspect the extraction script and the raw output files if necessary.

## Convention used here

The values labelled `P1`, `P2`, and `P3` in `summary.txt` are direct-lattice expansion coefficients, obtained after converting the FHI-aims reciprocal-direction output.
In other words, each coefficient multiplies the corresponding normalized direct-lattice vector when reconstructing the Cartesian polarization vector.

Consequently, `Delta P3` is the difference of endpoint third direct-lattice coefficients, not the Cartesian projection of `Delta P` onto the third direct-lattice vector.

## Inputs

`PBEsol/R-3c.extxyz` and `PBEsol/R3c.extxyz` are the endpoint structures.
`PBEsol/geometries/geometry.n=<N>.in` contains the interpolated geometry used for each calculation.

Regenerate the derived files only when deliberately repeating or changing the branch analysis.

## Extending the audit to every Table 1 functional

The `LDA/`, `PBE/`, and `HSE06/` directories contain prepared ten-image paths, generated from the independently relaxed endpoint structures used for their Table 1 rows.
Their `results/` directories are deliberately empty: no new FHI-aims calculations have been submitted by this setup.

`prepare_paths.py` constructs these paths reproducibly.
Before interpolation, it translates every polar-endpoint atom to its nearest periodic image relative to the reference endpoint; this is essential for a continuous path.
It derives a self-contained `control.in` from the corresponding Table 1 polarization-stage input, retaining its functional, numerical settings, and polarization grids while removing the unavailable ELSI restart read.

After generating `results/aims.n=0.out` through `results/aims.n=9.out` for a functional, run:

```bash
python3 -B extract_folded_polarization.py
```

This updates `folded_polarization.csv` and writes `verification-report.md`.
The report checks the branch continuity, reconstruction of the raw Cartesian FHI-aims polarization, rhombohedral component symmetry, and agreement with the rounded Table 1 values.
