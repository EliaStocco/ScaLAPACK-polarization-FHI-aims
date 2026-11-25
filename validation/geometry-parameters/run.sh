#!/usr/bin/env bash
# Regenerate the lattice and internal-site parameters of Tables S1-S4 with fd2bec.
# Requires fd2bec (see requirements.txt) and ASE in the active Python environment.
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")"

rm -rf geometries positions lattice.csv lattice.png
python prepare.py

# Lattice constants and angles of every structure.
space_group_dataset -i geometries/all.extxyz -o lattice.csv --plot-output lattice.png > space_group_dataset.log 2>&1

# Symmetry-allowed internal-site parameters, with the A-site atom at the origin.
# Cubic structures have no free internal parameters and are skipped.
mkdir -p positions
while read -r name; do
    [[ "${name}" == *_cubic_* ]] && continue
    tensor_symmetries -i "geometries/${name}.in" -n positions --precision 7 > "positions/${name}.txt" 2>&1
done < geometries/names.txt
