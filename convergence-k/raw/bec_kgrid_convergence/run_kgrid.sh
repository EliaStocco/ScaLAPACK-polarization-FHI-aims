#!/usr/bin/env bash
# Run one prepared k-grid using the CSC matrices from the reference SCF job.
set -euo pipefail

: "${AIMS:?Set AIMS to the FHI-aims executable before running this script.}"
script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
calculation_dir="${1:-${PWD}}"
density_dir="${script_dir}/density-matrix"

if [[ ! -f "${calculation_dir}/sourceme.sh" ]]; then
    echo "Prepared k-grid directory not found: ${calculation_dir}" >&2
    exit 1
fi

if ! find -H "${calculation_dir}/geometries" -maxdepth 1 -type f \
        -name 'geometry.n=*.in' -print -quit | grep -q .; then
    echo "No prepared geometries found via ${calculation_dir}/geometries." >&2
    exit 1
fi

shopt -s nullglob
density_matrices=("${density_dir}"/*.csc)
shopt -u nullglob
if (( ${#density_matrices[@]} == 0 )); then
    echo "No saved density matrices found in ${density_dir}." >&2
    exit 1
fi

(
    cd "${calculation_dir}"
    cp -- "${density_matrices[@]}" .
    source sourceme.sh
)
