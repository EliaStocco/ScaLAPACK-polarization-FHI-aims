# New-m alltoall=false load-balanced scaling analysis

`analyze.py` extracts the final FHI-aims wall times from the successful
`results/aims.n=*.out` files, pairs SCF and dipole runs, and fits
`time = A * ncores**m` in log--log space.  Polarization overhead is defined
as `dipole - SCF`.  For the overall SCF and dipole times, the **second** value
on the final `| Total time : ... s ... s` line is used. Dipole-internal timers are summed over the three reciprocal
lattice directions.  Backup directories are intentionally excluded.

The extraction found 90 usable timing records and 45 SCF/dipole pairs.  The
`revPBE0, m=196` series has no usable files; the other series have between
3 and 8 core-count points depending on completed runs.

## Polarization scaling exponents

| Functional | Molecules | Points | exponent `m` | R² |
| --- | ---: | ---: | ---: | ---: |
| HSE06 | 128 | 8 | -0.602 | 0.986 |
| HSE06 | 196 | 5 | -0.442 | 0.762 |
| HSE06 | 256 | 4 | -0.625 | 0.993 |
| revPBE | 128 | 8 | -0.674 | 0.993 |
| revPBE | 196 | 8 | -0.798 | 0.996 |
| revPBE | 256 | 4 | -0.664 | 0.985 |
| revPBE0 | 128 | 5 | -0.449 | 0.982 |
| revPBE0 | 256 | 3 | -0.559 | 0.988 |

All measured polarization series scale slower than ideal inverse scaling
(`m=-1`).  The best observed series is revPBE, 196 molecules (`m=-0.799`),
while revPBE0, 128 molecules is the least scalable (`m=-0.450`).  The
Fourier-interpolated eigenvalue timer is consistently a major non-ideal
component; inspect `component-scalability.csv` for every fitted component,
prefactor, fit quality, and per-doubling time factor.

## Outputs

* `dataframe.csv`: all extracted SCF and dipole records.
* `analysis-dataframe.csv`: paired runs and derived overhead/components.
* `fit.json`: power-law parameters.
* `scaling.pdf`: overview of polarization overhead scaling.
* `components-*.pdf`: per-functional/per-system component breakdowns.

Regenerate with:

```bash
python3 analyze.py
```
