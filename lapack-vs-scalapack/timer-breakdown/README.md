# Figure 5 timer breakdown

This directory compares the wall-clock timers of the polarization calculation for the 2x2x2 system with a 2x2x16 dipole grid.
`ScaLAPACK` values are extracted from the original Figure 5 outputs in `../dipole/scalapack/`.
`LAPACK` values are extracted from the final timer-corrected rerun at `viper:/viper/ptmp1/elsto/works/ScaLAPACK-comparison/2x2x2/dipole-2x2x16/lapack-rerun-recompiled-executable-bugfix2`.

A copy of that directory (without the restart matrices) is stored in `lapack-rerun/`.
Regenerate the data and figure with:

```bash
python extract_component_times.py lapack-rerun
python plot_component_times.py
```

The canonical plot is `Figure-5-components.pdf`.
