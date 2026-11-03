# BaTiO3 scaling-analysis bundle

This bundle contains the raw FHI-aims outputs supporting the current timing table,
the derived CSV data, and scripts that rebuild and plot the fits.

Run:

```bash
python3 build_dataset.py
python3 plot_scaling.py
python3 plot_component_scaling.py
```

`plot_scaling.py` and `plot_component_scaling.py` require matplotlib (`pip install -r requirements.txt`).

The fit is a least-squares line in log--log space for
`polarization_time_s = dipole_time_s - scf_time_s`, reported as the non-negative
scaling power `p` in `t = C N^{-p}`.

`scaling_summary.csv` also contains separate log--log non-negative scaling powers `p` and R² values for
FHI-aims' final maximum wall-clock timers: Fourier-interpolated eigenvalue solution,
dipole-matrix construction, Berry term, and dipole term. The component times are
columns in `timing_data.csv`. That CSV also provides the signed `extra_cost_s` residual, defined as `polarization_time_s - sum(component_time_s)`. The summary additionally fits the magnitude of this signed residual as `|extra_cost_s| = C N^{-p}`; it is a diagnostic fit and may have a poor R² when independent runs differ substantially. For each component and the signed residual, `timing_data.csv` reports raw percentage shares and `scaling_summary.csv` reports their ranges. The four raw component shares sum to 100% at each core count by construction: their denominator is the sum of the four component timers. The summary retains fitted percentage-share ranges as a separate diagnostic: `100 * fitted_component_time / fitted_polarization_time`, evaluated at every measured core count. A zero component time has no log--log exponent and is
left blank (currently the Berry term for the `3 2 1 1` meshes).

`raw/` preserves the original workspace-relative paths of every output used in the
analysis. `scaling_summary.csv` also records the largest FHI-aims tracked-memory maximum across each series, reported in MB and GiB per MPI rank, plus a rank-maximum-times-128 GiB-per-node estimate and its percentage of the Slurm capacity for the partition used by that peak-memory run; these are code-tracked values, not Slurm MaxRSS. `raw_files_manifest.csv` maps each retained raw output to the series that
use it. The 4x4x4 HSE06 `3 4 2 2` series uses the coallocated SCF/dipole reruns;
the 8x8x8 HSE06 128-core points use hugemem, while its 512--2048-core points use
largemem. The 256-core hugemem HSE06 runs were still pending when this bundle was made.


## Publication-ready table

`scaling_table_raw_shares.tex` is a standalone landscape table with the raw
contribution-share ranges. It uses blue LDA rows, orange HSE06 rows, and a heavy
rule between the 4x4x4 and 8x8x8 series. Compile it in this directory with:

```bash
latexmk -pdf scaling_table_raw_shares.tex
```

The accompanying `latexmkrc` sets non-interactive PDF compilation options.
