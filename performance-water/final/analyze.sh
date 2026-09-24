#!/usr/bin/env bash
# Regenerate all analysis products from the FHI-aims output files.
set -euo pipefail

script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
export MPLCONFIGDIR="${TMPDIR:-/tmp}/fhi-aims-water-matplotlib"
mkdir -p "$MPLCONFIGDIR"

python3 "$script_dir/extract.py"
python3 "$script_dir/fit-dataframe.py"
python3 "$script_dir/plot.py"
python3 "$script_dir/plot-all.py"
python3 "$script_dir/plot-components.py"
