# ScaLAPACK-polarization-FHI-aims

## Manuscript figures

The scripts below regenerate the data-derived figures used by the companion
LaTeX manuscript in `/home/stoccoel/Documents/LaTeX/ScaLAPACK`. Main-text
figures use `figures/Figure-<n>.pdf` and supplementary figures use
`figures/Figure-S<n>.pdf`; run the commands from this repository root.

| Draft figure | Script | Output |
| --- | --- | --- |
| Figure 3 | `python3 spline/plot.py` | `spline/Figure-3.pdf` |
| Figure 5 | `python3 comparison/2x2x16/plot.py` | `comparison/2x2x16/Figure-5.pdf` |
| Figure 6 | `python3 scaling-atoms/plot-left_top.py` | `scaling-atoms/Figure-6.pdf` |
| Figure 7 | `python3 viper-polarization-scaling-20261118/plot_figure7.py` | `viper-polarization-scaling-20261118/Figure-7.pdf` |
| Figure S1 | `python3 scaling-atoms/plot_right.py` | `scaling-atoms/Figure-S1.pdf` |
| Figure S2 | `python3 performance-water/final-alltoall-load/plot.py` | `performance-water/final-alltoall-load/water.pdf` |
| Figure S3 functional comparison | `python3 viper-polarization-scaling-20261118/plot_functional_ratios.py` | `viper-polarization-scaling-20261118/Figure-S3-functional-ratios.pdf` |

Figures 1, 2, and 4 are conceptual TikZ diagrams maintained in the manuscript
repository, not Python outputs. Regenerate them from the manuscript root with
`./figures/build-figures.sh`; it removes all LaTeX by-products automatically.

Before regenerating a plot, install the packages listed in
`requirements.txt` and refresh the input CSV data when needed. Each script
writes its canonical PDF beside its data and source code. The matching entry
in `figures/` is a relative symbolic link, and the manuscript workspace links
to that entry; regenerating a canonical PDF updates the manuscript asset
immediately.
