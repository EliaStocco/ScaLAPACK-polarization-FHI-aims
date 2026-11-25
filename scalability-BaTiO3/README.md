# Viper BaTiO3 polarization-scaling bundle

This bundle contains the timing-relevant FHI-aims outputs downloaded on 2026-11-18 from the Viper campaign at
`/viper/ptmp1/elsto/works/ScaLAPACK-performance/BaTiO3/new-time-vs-cores/`.

The included raw text outputs correspond to the following calculations:

| Supercell | Functional | SCF grid | Polarization grid |
|---|---|---|---|
| 4x4x4 | LDA | 2x2x2 | `3 2 2 4` |
| 4x4x4 | HSE06 | 2x2x2 | `3 2 2 4` |
| 8x8x8 | LDA | 1x1x1 | `3 1 1 2` |
| 8x8x8 | HSE06 | 1x1x1 | `3 1 1 2` |

`raw/` preserves the polarization and matching standalone-SCF outputs needed for the analysis, together with the relevant input and job files.
The 65 GB HSE06 density snapshot was intentionally excluded because it is not needed to reproduce the timings.
The 8x8x8 LDA 128-core calculation is omitted because it ended with an out-of-memory failure.
The 8x8x8 HSE06 runs originate from the `hse06-unconverged` campaign directory and must be interpreted accordingly.

## Timing definition

For every available core count, `fit_scaling.py` extracts the final whole-run wall time from the `Detailed time accounting` block of each FHI-aims output and computes

```text
net polarization time = (SCF + polarization whole-run time) - (standalone-SCF whole-run time).
```

For the 4x4x4 HSE06 series, the standalone-SCF reruns named `aims.repeat-20261101.n=128.out` and `aims.repeat-20261101.n=512.out` are used at 128 and 512 cores, respectively.
They agree with the non-WCC portion of the corresponding polarization jobs, unlike the first SCF attempts.

## Regeneration

Run from this directory:

```bash
bash run_all.sh
```

`run_all.sh` uses the `eslib` Python environment by default; set `PYTHON` to override it.
It writes `timing_data.csv`, `scaling_summary.csv`, the Figure 7 data adapters, and all Figure 7 and component PDFs, including `Figure-S3-functional-ratios.pdf`.
`plot_figure7_left_only.py` produces the main-text Figure 7 from the Viper data, while `plot_figure7_dense_grid.py` produces the Supplemental-Material panel from the original denser-grid reference data.
