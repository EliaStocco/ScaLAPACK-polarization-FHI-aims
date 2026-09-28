#!/usr/bin/env bash
# Run the one reference SCF calculation that produces the shared CSC files.
set -euo pipefail

: "${AIMS:?Set AIMS to the FHI-aims executable before running this script.}"
script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
density_dir="${script_dir}/density-matrix"
output_file="${density_dir}/results/aims.n=0.out"

if [[ -f "${output_file}" ]] && grep -q "Have a nice day." "${output_file}"; then
    echo "Keeping completed reference density calculation: ${output_file}"
    exit 0
fi

(
    cd "${density_dir}"
    srun "${AIMS}" > aims.out 2>&1
    cp aims.out results/aims.n=0.out

    shopt -s nullglob
    density_matrices=( *.csc )
    shopt -u nullglob
    if (( ${#density_matrices[@]} == 0 )); then
        echo "FHI-aims completed but did not create any CSC density matrices." >&2
        exit 1
    fi
)
