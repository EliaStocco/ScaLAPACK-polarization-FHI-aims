#!/usr/bin/env bash
set -euo pipefail
python_bin="${PYTHON:-/home/stoccoel/.pyenv/versions/eslib/bin/python3.9}"
"$python_bin" fit_scaling.py
"$python_bin" prepare_figure7_left_panel_data.py
"$python_bin" plot_figure7_left_only.py
"$python_bin" plot_figure7_dense_grid.py
"$python_bin" plot_scaling.py
"$python_bin" plot_exponents.py
"$python_bin" extract_components.py
"$python_bin" prepare_figure7_component_data.py
"$python_bin" plot_component_scaling.py
"$python_bin" plot_component_exponents.py
"$python_bin" plot_functional_ratios.py
