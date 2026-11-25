#!/usr/bin/env bash
set -euo pipefail
python3 fit_scaling.py
python3 prepare_figure7_left_panel_data.py
python3 plot_figure7.py
python3 plot_scaling.py
python3 plot_exponents.py
python3 extract_components.py
python3 prepare_figure7_component_data.py
python3 plot_component_scaling.py
python3 plot_component_exponents.py
