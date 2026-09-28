#!/usr/bin/env bash
# Submit the reference density job and one dependent job for every k-grid.
set -euo pipefail

script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"

if ! command -v sbatch > /dev/null; then
    echo "sbatch is not available in PATH." >&2
    exit 1
fi
if [[ ! -f "${script_dir}/density-matrix/control.in" ]]; then
    echo "Missing density-matrix inputs. Run ./prepare_density.sh first." >&2
    exit 1
fi

mkdir -p "${script_dir}/slurm" "${script_dir}/density-matrix/slurm"
for calculation_dir in "${script_dir}"/k-grid-*; do
    [[ -f "${calculation_dir}/sourceme.sh" ]] || continue
    mkdir -p "${calculation_dir}/slurm"
done

density_submission="$(sbatch --parsable --chdir="${script_dir}" "${script_dir}/run_density.slurm")"
density_job_id="${density_submission%%;*}"
echo "Submitted density-matrix job ${density_job_id}"

for calculation_dir in "${script_dir}"/k-grid-*; do
    [[ -f "${calculation_dir}/sourceme.sh" ]] || continue
    grid_name="${calculation_dir##*/}"
    grid_submission="$(sbatch \
        --parsable \
        --chdir="${calculation_dir}" \
        --dependency="afterok:${density_job_id}" \
        --job-name="bec-${grid_name}" \
        "${script_dir}/run_kgrid.slurm")"
    echo "Submitted ${grid_name} job ${grid_submission%%;*} afterok:${density_job_id}"
done
