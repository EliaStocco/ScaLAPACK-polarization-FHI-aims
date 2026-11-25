#!/bin/bash
set -euo pipefail

run_root="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source_root="$(cd "${run_root}/.." && pwd)"
restart_root="$(cd "${source_root}/../converge" && pwd)"
aims_exe="${source_root}/FHI-aims/build/aims.260527.scalapack.mpi.x"
walltime="00:45:00"

test -x "${aims_exe}"
test -d "${restart_root}"

for cores in 8 16 32 64 128 256 512 1024; do
    if (( cores <= 128 )); then
        nodes=1
    elif (( cores == 256 )); then
        nodes=2
    elif (( cores == 512 )); then
        nodes=4
    else
        nodes=8
    fi

    case_dir="${run_root}/n=${cores}"
    if [[ -e "${case_dir}" ]]; then
        echo "Refusing to overwrite existing ${case_dir}" >&2
        exit 1
    fi

    mkdir -p "${case_dir}/slurm"
    cp -p "${source_root}/lapack/control.in" "${source_root}/lapack/geometry.in" "${case_dir}/"
    for restart_file in "${restart_root}"/*.csc; do
        ln -s "${restart_file}" "${case_dir}/$(basename "${restart_file}")"
    done

    job_id=$(sbatch \
        --job-name="MgO-lapack-new-n${cores}" \
        --nodes="${nodes}" \
        --ntasks-per-node=128 \
        --time="${walltime}" \
        --output="${case_dir}/slurm/output.txt" \
        --error="${case_dir}/slurm/error.txt" \
        --chdir="${case_dir}" \
        --export="ALL,NUM_CORES=${cores},AIMS_EXE=${aims_exe}" \
        "${run_root}/job.sh")
    printf '%s\n' "${job_id}" | tee "${run_root}/submissions/n=${cores}.txt"
done
