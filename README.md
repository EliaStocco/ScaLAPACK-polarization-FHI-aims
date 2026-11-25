# Reproduction data for the ScaLAPACK Berry-phase polarization manuscript

This branch contains only the FHI-aims outputs, extracted data and scripts
needed to regenerate the data figures and tables of the manuscript
"Scalable Berry-Phase Polarization Calculations with Numeric Atomic Orbitals"
and its supplementary material.

Install the Python packages in `requirements.txt` first.
The plotting scripts read `style.mplstyle` from the repository root and use
LaTeX for text rendering.
Every extraction step below regenerates the committed CSV/JSON files exactly
from the FHI-aims outputs in this branch.
The manuscript figures were produced with Python 3.9 and matplotlib 3.9.4,
except Figure S4 (Python 3.11, matplotlib 3.6.3); other versions can change
the layout slightly (by a few pixels) but not the data.

## Figures

Figures 1, 2 and 4 and the Berry-phase link schematic are TikZ diagrams kept
in the manuscript repository; they are not data plots.

| Figure | Extraction (run in the directory) | Plot | Output |
| --- | --- | --- | --- |
| 3 | `spline/`: `python extract.py` | `python spline/plot.py` | `spline/Figure-3.pdf` |
| 5 | `lapack-vs-scalapack/`: `python extract.py` | `python lapack-vs-scalapack/plot.py` | `lapack-vs-scalapack/Figure-5.pdf` |
| 6 | `scaling-atoms/`: `python extract.py` | `python scaling-atoms/plot-left_top.py` | `scaling-atoms/Figure-6.pdf` |
| 7, S3, S5 | `scalability-BaTiO3/`: `PYTHON=python bash run_all.sh` | (included in `run_all.sh`) | `Figure-7-left-only.pdf`, `Figure-7-components-ideal.pdf`, `Figure-S4-dense-k-grid-scalability.pdf` |
| S1 | `lapack-vs-scalapack/timer-breakdown/`: `python extract_component_times.py lapack-rerun` | `python lapack-vs-scalapack/timer-breakdown/plot_component_times.py` | `lapack-vs-scalapack/timer-breakdown/Figure-5-components.pdf` |
| S2 | `scaling-atoms/`: `python extract.py` | `python scaling-atoms/plot_right.py` | `scaling-atoms/Figure-S1.pdf` |
| S4 | `scalability-water/`: `python extract.py && python fit-dataframe.py` | `python scalability-water/plot.py` | `scalability-water/water.pdf` |

Plot commands are run from the repository root.
Output file names follow the producing scripts and differ from the
supplementary figure numbers.

Notes:

- Figure 6 and S2 use the 8x8x8 reruns with polarization along direction 1
  (`scaling-atoms/supercell-8x8x8/*/dipole/rerun-20261120-dir1*`), selected in
  `scaling-atoms/extract.py`.
- Figure S1: the ScaLAPACK timers come from the outputs in
  `lapack-vs-scalapack/dipole/scalapack/`; the LAPACK timers come from the
  timer-corrected rerun in
  `lapack-vs-scalapack/timer-breakdown/lapack-rerun/`.
- The reference data used by Figures 7, S3 and S5
  (`scalability-BaTiO3/reference_*`) are copies of
  `scalability-BaTiO3-dense-grid/dataframe.csv`, `scalability-BaTiO3-dense-grid/fit.json` and
  `scalability-BaTiO3-dense-grid-components/dense_component_data.csv`.
  `scalability-BaTiO3-dense-grid/extract.py` followed by `fit-dataframe.py` (run in
  `scalability-BaTiO3-dense-grid/`) and
  `scalability-BaTiO3-dense-grid-components/extract_dense_components.py` regenerate them
  exactly.

## Tables

The table values were transcribed into the manuscript from the files below.

| Table | Source data | Regeneration |
| --- | --- | --- |
| I (polarization) | `validation/BaTiO3.{csv,txt}`, `validation/BaTiO3-t.{csv,txt}`, `validation/BiFeO3.txt`, `validation/BiFeO3/polarization_difference.csv`, `validation/PbTiO3.txt`, `validation/PbTiO3-path/folded_polarization.csv` | `validation/`: `bash run.sh` |
| II (lattice constants, Born effective charges) | `BEC/{MgO,BaTiO3}/{LDA,PBE,PBEsol}/bec/bec.txt`, `bec/geometry.in`, `relax/` | `bec.txt` is written by `post_process_aims` from the fd2bec package (<https://github.com/EliaStocco/fd2bec>), using the outputs in `bec/results/` |
| III (core-scalability exponents) | `scalability-BaTiO3/scaling_summary.csv`, `timing_data.csv` | `scalability-BaTiO3/fit_scaling.py` (part of `run_all.sh`) |
| S1–S4 (geometries) | relaxed `geometry.in` files under `validation/{BaTiO3,PbTiO3,BiFeO3}/**/lapack/`; fd2bec outputs in `validation/geometry-parameters/` | `validation/geometry-parameters/`: `bash run.sh` (see its README for the mapping to the table columns) |

Table III: the exponents are the column `p` of
`scalability-BaTiO3/scaling_summary.csv`, and their
uncertainties are the standard errors of the log–log slopes in the column
`p_stderr` of the same file.
