# Water polarization component scaling

This directory contains strong-scaling measurements for liquid-water
polarization calculations. This note discusses only the revPBE and revPBE0
results; HSE06 is intentionally excluded.

## Take-home message

The Fourier-interpolated eigenvalue solution is the main obstacle to nearly
ideal strong scaling. It is the largest timed internal component at 2048 cores
for every revPBE/revPBE0 series (about 77--82% of the polarization overhead),
and it scales substantially more slowly than the ideal `time ∝ ncores^-1`.

The dipole-matrix calculation is the secondary bottleneck. The dipole and
Berry terms are smaller; for the 196-molecule revPBE case they are close to
ideal scaling and therefore do not determine the total behavior.

## Method

`extract.py` reads the total SCF and dipole calculation wall times and the
internal polarization timers. Internal timers are summed over the three
polarization directions in each calculation. The polarization overhead is
defined as

```text
polarization time = dipole total time - SCF total time.
```

For every functional, water-box size, and timing component, the analysis fits

```text
time = A * ncores^m
```

in log--log space. Ideal strong scaling has `m = -1`: doubling the number of
cores halves the time. Values closer to zero therefore indicate poorer
scaling. The fitted parameters and their log--log fit quality are in
[`component-scalability.csv`](component-scalability.csv), ordered from most to
least non-ideal.

`Extra` is the absolute difference between the end-to-end polarization
overhead and the internal Wannier timer. It represents uninstrumented work
and timer/run-to-run differences; it is useful for checking reconciliation,
but should not be interpreted as a separately identified computational
component.

## Fitted exponents

| Functional | Molecules | Polarization total | Fourier interpolation | Dipole matrix | Dipole term | Berry term | SCF total |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| revPBE | 128 | -0.512 | -0.423 | -0.600 | -0.661 | -0.602 | -0.498 |
| revPBE | 196 | -0.669 | -0.603 | -0.660 | -0.965 | -0.908 | -0.574 |
| revPBE0 | 128 | -0.432 | -0.336 | -0.476 | -0.423 | -0.392 | -0.577 |
| revPBE0 | 196 | -0.506 | -0.475 | -0.518 | -0.744 | -0.690 | -0.693 |

The Fourier term is consistently the slowest-scaling major component. Its
exponent ranges from `-0.336` to `-0.603`, so a doubling of cores reduces its
time by only 21--34%, rather than the ideal 50%. The dipole matrix generally
scales somewhat better (`-0.476` to `-0.660`), but is still non-ideal.

For revPBE with 196 molecules, the dipole and Berry terms scale nearly
ideally (`m = -0.965` and `-0.908`), showing that these two terms are not the
primary cause of the poor total scaling. The same components scale less well
in the smaller system and with revPBE0, but they remain much smaller than the
Fourier contribution at high core count.

SCF total time also scales sub-ideally (`m = -0.498` to `-0.693`). It affects
the total job wall time, but it is not the source of the polarization-overhead
bottleneck.

## Outputs and regeneration

The per-series breakdown plots are in
[`component-plots/`](component-plots/), with one PDF for every functional and
water-box size. Regenerate all derived files from the raw FHI-aims outputs
with:

```bash
bash analyze.sh
```

This runs the extraction, power-law fitting, standard scaling plots, component
plots, and the CSV summary.
