#!/usr/bin/env bash
# Create one finite-difference FHI-aims calculation per polarization k-grid.
set -euo pipefail

script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
readonly scf_grid=(8 8 8)
# The Berry-phase string length must exceed the fixed SCF grid.
readonly polarization_grids=(16 20 24 28 32 36 40 48 56 64 80)
shared_geometries="${script_dir}/geometries"

share_geometries() {
    local calculation_dir="$1"
    local geometry_dir="${calculation_dir}/geometries"
    local sourceme_file="${calculation_dir}/sourceme.sh"

    if [[ -f "${sourceme_file}" ]]; then
        sed -i 's/find geometries -maxdepth 1/find -H geometries -maxdepth 1/' "${sourceme_file}"
    fi

    if [[ ! -d "${shared_geometries}" ]]; then
        mv "${geometry_dir}" "${shared_geometries}"
    elif [[ ! -L "${geometry_dir}" ]]; then
        rm -rf -- "${geometry_dir}"
    fi

    if [[ ! -L "${geometry_dir}" ]]; then
        ln -s ../geometries "${geometry_dir}"
    fi
}

for n in "${polarization_grids[@]}"; do
    calculation_dir="${script_dir}/k-grid-${n}"
    mkdir -p "${calculation_dir}/results"
    if [[ -f "${calculation_dir}/sourceme.sh" ]]; then
        cp "${calculation_dir}/control.other.in" "${calculation_dir}/control.first.in"
        share_geometries "${calculation_dir}"
        echo "Keeping existing preparation: ${calculation_dir}"
        continue
    fi

    cp "${script_dir}/reference.extxyz" "${calculation_dir}/reference.extxyz"
    # The older convergence template uses ``kkk`` placeholders in these
    # lines.  prepare_aims writes the three grid-specific lines below.
    sed '/^[[:space:]]*output[[:space:]]\+polarization[[:space:]]/d' \
        "${script_dir}/../aims.in" > "${calculation_dir}/control.in"

    (
        cd "${calculation_dir}"
        prepare_aims \
            -i reference.extxyz \
            --what bec \
            --k-grid "${scf_grid[@]}" \
            --k-grid-polarization "${n}" "${n}" "${n}" \
            --use-csc
        # A common reference density is staged by main.sh.  Make the first
        # displaced calculation read it too, rather than writing a new CSC
        # restart file inside every k-grid calculation.
        cp control.other.in control.first.in
    )
    share_geometries "${calculation_dir}"
done
