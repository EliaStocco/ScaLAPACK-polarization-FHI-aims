# Reproduction data for the ScaLAPACK Berry-phase polarization manuscript

This branch contains only the FHI-aims outputs, extracted data and scripts
needed to regenerate the data figures and tables of the manuscript
"Scalable Implementation of Berry-Phase Polarization with Localized Atomic
Orbitals" and its supplementary material.

Install the Python packages in `requirements.txt` first.
The plotting scripts read `style.mplstyle` from the repository root and use
LaTeX for text rendering.
Every extraction step below regenerates the committed CSV/JSON files exactly
from the FHI-aims outputs in this branch.

## Figures

Figures 1, 2 and 4 and the Berry-phase link schematic are TikZ diagrams kept
in the manuscript repository; they are not data plots.

| Figure | Extraction (run in the directory) | Plot | Output |
| --- | --- | --- | --- |
| 3 | `spline/`: `python extract.py` | `python spline/plot.py` | `spline/Figure-3.pdf` |
| 5 | `comparison/2x2x16/`: `python extract.py` | `python comparison/2x2x16/plot.py` | `comparison/2x2x16/Figure-5.pdf` |
| 6 | `scaling-atoms/`: `python extract.py` | `python scaling-atoms/plot-left_top.py` | `scaling-atoms/Figure-6.pdf` |
| 7, S3, S5 | `viper-polarization-scaling-20261118/`: `PYTHON=python bash run_all.sh` | (included in `run_all.sh`) | `Figure-7-left-only.pdf`, `Figure-7-components-ideal.pdf`, `Figure-S4-dense-k-grid-scalability.pdf` |
| S1 | `comparison/2x2x16/timer-breakdown-20261118/`: `python extract_component_times.py lapack-rerun-recompiled-executable-bugfix2` | `python comparison/2x2x16/timer-breakdown-20261118/plot_component_times.py` | `comparison/2x2x16/timer-breakdown-20261118/Figure-5-components.pdf` |
| S2 | `scaling-atoms/`: `python extract.py` | `python scaling-atoms/plot_right.py` | `scaling-atoms/Figure-S1.pdf` |
| S4 | `performance-water/final-alltoall-load/`: `python extract.py && python fit-dataframe.py` | `python performance-water/final-alltoall-load/plot.py` | `performance-water/final-alltoall-load/water.pdf` |

Plot commands are run from the repository root.
Output file names follow the producing scripts and differ from the
supplementary figure numbers.

Notes:

- `comparison/2x2x16/scf` is a symbolic link to `comparison/2x2x20/scf`.
- Figure 6 and S2 use the 8x8x8 reruns with polarization along direction 1
  (`scaling-atoms/supercell-8x8x8/*/dipole/rerun-20261120-dir1*`), selected in
  `scaling-atoms/extract.py`.
- Figure S1: the ScaLAPACK timers come from the outputs in
  `comparison/2x2x16/dipole/scalapack/`; the LAPACK timers come from the
  timer-corrected rerun in
  `comparison/2x2x16/timer-breakdown-20261118/lapack-rerun-recompiled-executable-bugfix2/`.
- The reference data used by Figures 7, S3 and S5
  (`viper-polarization-scaling-20261118/reference_*`) are copies of
  `performance-BaTiO3/dataframe.csv`, `performance-BaTiO3/fit.json` and
  `scaling-comparison_20261104/dense_component_data.csv`.
  `performance-BaTiO3/extract.py` followed by `fit-dataframe.py` (run in
  `performance-BaTiO3/`) and
  `scaling-comparison_20261104/extract_dense_components.py` regenerate them
  exactly.

## Tables

The table values were transcribed into the manuscript from the files below.

| Table | Source data | Regeneration |
| --- | --- | --- |
| I (polarization) | `validation/BaTiO3.{csv,txt}`, `validation/BaTiO3-t.{csv,txt}`, `validation/BiFeO3.txt`, `validation/BiFeO3/polarization_difference.csv`, `validation/PbTiO3.txt`, `validation/test-PbTiO3/folded_polarization.csv` | `validation/`: `bash run.sh` |
| II (lattice constants, Born effective charges) | `BEC/{MgO,BaTiO3}/{LDA,PBE,PBEsol}/bec/bec.txt`, `bec/geometry.in`, `relax/` | `bec.txt` is written by `post_process_aims` from the external fd2bec package (not included) |
| III (core-scalability exponents) | `viper-polarization-scaling-20261118/scaling_summary.csv`, `timing_data.csv` | `viper-polarization-scaling-20261118/fit_scaling.py` (part of `run_all.sh`) |
| S1–S4 (geometries) | relaxed `geometry.in` files under `validation/{BaTiO3,PbTiO3,BiFeO3}/**/{lapack,relax}/` | lattice and internal-site parameters computed from these geometries |

The uncertainties of the exponents in Table III are the standard errors of the
log–log slopes fitted to `timing_data.csv`.
