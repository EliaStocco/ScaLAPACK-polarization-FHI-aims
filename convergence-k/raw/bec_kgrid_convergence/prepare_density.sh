#!/usr/bin/env bash
# Prepare the single reference calculation that writes the shared CSC files.
set -euo pipefail

script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
density_dir="${script_dir}/density-matrix"

mkdir -p "${density_dir}/results"
cp "${script_dir}/reference.extxyz" "${density_dir}/reference.extxyz"
# Keep the supplied basis and 8x8x8 SCF grid, but omit Berry-phase output:
# this calculation exists only to converge and save the SCF density matrix.
sed \
    -e '/^[[:space:]]*output[[:space:]]\+polarization[[:space:]]/d' \
    -e '/^[[:space:]]*elsi_restart[[:space:]]/d' \
    "${script_dir}/../aims.in" > "${density_dir}/control.in"
printf '\nelsi_restart write scf_converged\n' >> "${density_dir}/control.in"

(
    cd "${density_dir}"
    extxyz2folder -i reference.extxyz -f aims -o geometries
    cp geometries/geometry.n=0.in geometry.in
)
