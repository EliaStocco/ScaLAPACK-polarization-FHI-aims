# BaTiO3 polarization component scaling

This is the component-level strong-scaling analysis for the BaTiO3 `4x4x4` and `8x8x8` supercells. It uses FHI-aims maximum CPU time, matching the existing BaTiO3 scaling plot.

## Take-home message

BaTiO3 scales much more nearly ideally than the water calculations.

- The `8x8x8` polarization overhead has `m = -0.963`, essentially ideal inverse scaling (`m = -1`).
- The `4x4x4` polarization overhead has `m = -0.829`: good strong scaling, but modestly slower than ideal.
- Fourier interpolation is the only sizable component that explains this deviation in `4x4x4`. At 2048 cores, it is 68--72% of the polarization overhead and has `m = -0.710` for `4x4x4`.
- The `4x4x4` dipole-matrix timer scales poorly (`m = -0.316`), but it is only 7% of the polarization overhead at 2048 cores; it therefore does not materially limit the total.
- The dipole and Berry terms are near ideal in both supercells.

## Method

[`analyze-components.py`](analyze-components.py) pairs SCF and dipole outputs with identical supercell and core counts. The end-to-end polarization overhead is:

```text
polarization time = dipole total time - SCF total time.
```

It reads the internal Wannier, Fourier-interpolation, dipole-matrix, dipole-term, and Berry-term timers. If an output has more than one polarization-direction block, its component times are summed. Each series is fitted in log--log space to `time = A * ncores^m`; ideal strong scaling has `m = -1`.

The analysis uses seven paired core counts for `4x4x4` and four for `8x8x8`. `Extra` is the absolute residual between the end-to-end polarization overhead and the Wannier timer. It represents uninstrumented work and timer/run-to-run differences, not an identified computational component. Its extreme exponent for `8x8x8` is an artefact of fitting a small residual.

## Fitted exponents

| Supercell | Polarization total | Fourier interpolation | Dipole matrix | Dipole term | Berry term | SCF total |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 4x4x4 | -0.829 | -0.710 | -0.316 | -0.955 | -0.914 | -0.602 |
| 8x8x8 | -0.963 | -0.926 | -0.780 | -1.107 | -1.018 | -0.829 |

The `8x8x8` Fourier term is itself near ideal (`m = -0.926`) and dominates the total, explaining the near-ideal polarization scaling. For `4x4x4`, Fourier interpolation is slower and sets the overall deviation. SCF total time is slower than ideal, especially for `4x4x4`, but it affects the full calculation time rather than the dipole-minus-SCF polarization overhead considered here.

## Outputs and regeneration

- [`component-dataframe.csv`](component-dataframe.csv) contains paired raw component timings.
- [`component-scalability.csv`](component-scalability.csv) contains fitted exponents, errors, log--log R² values, and ideal-scaling deviations.
- [`component-plots/`](component-plots/) contains one breakdown PDF per supercell.

Regenerate with:

```bash
python3 analyze-components.py
```
