# Corrected-polarization scaling bundle

This archive contains the non-dense-SCF-grid campaign with the polarization
direction corrected:

| Supercell | SCF k-grid | Polarization grid |
|---|---|---|
| 4x4x4 | 2x2x2 | `3 2 2 4` |
| 8x8x8 | 1x1x1 | `3 1 1 2` |

`raw/` contains the FHI-aims outputs for the available points and the matching
standalone SCF outputs.  The 8x8x8 LDA 128-core point and HSE06 256/2048-core
points are not included because they do not have completed results.  The HSE06
8x8x8 points were run from an unconverged density and should be treated as
preliminary.

This clean folder also contains plotting scripts that use the corrected timing
data:

- `plot_scaling.py` writes `Figure-7-corrected-scalability.pdf`, a four-panel
  Figure 7-style core-count plot with fitted curves and ideal-scalability guides.
- `plot_exponents.py` writes `Figure-7-corrected-exponents.pdf`, a summary of
  the fitted strong-scalability exponents.
- `plot_figure7_comparison.py` writes `Figure-7-corrected-vs-old.pdf`, with the
  corrected campaign in the left panel and the original Figure 7 data in the
  right panel.  The original timing data are copied locally as
  `reference_timing_data.csv`.
- `extract_components.py` reads the internal timers from the raw corrected logs.
- `plot_component_scaling.py` writes corrected-data versions of
  `Figure-7-components-ideal.pdf`, `Figure-7-component-shares.pdf`, and
  `Figure-7-component-exponents.pdf`.

The component figures are direct replacements for the original Figure 7
companion plots, using only the corrected campaign data.  The optional
`plot_figure7_comparison.py` script is retained for ad hoc comparisons, but is
not run by `run_all.sh`.

Run everything from this directory:

```bash
bash run_all.sh
```

This writes `timing_data.csv` and `scaling_summary.csv`.  The fitted convention
is `t_pol = C * N^(-p)`, so `p` is reported non-negative; `R2` is the log-log
coefficient of determination.  Here `t_pol` is the corrected-grid combined
SCF/polarization runtime minus the matching standalone SCF runtime.

The four corrected series are 4x4x4/LDA, 4x4x4/HSE06, 8x8x8/LDA, and
8x8x8/HSE06.  The available core counts are determined from the raw files;
missing campaign points are omitted automatically.
