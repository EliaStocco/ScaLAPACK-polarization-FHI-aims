#!/bin/bash -l
#SBATCH -o slurm/output.txt
#SBATCH -e slurm/error.txt
#SBATCH -D ./
#SBATCH -J pol-1x1x1
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=72
#SBATCH --mail-type=NONE
#SBATCH --time=02:00:00

set -euo pipefail

mkdir -p slurm results
module purge
module load intel/2024.0
module load impi/2021.11
module load mkl/2024.0
export LD_LIBRARY_PATH="${MKL_HOME}/lib/intel64:${LD_LIBRARY_PATH:-}"
export LD_LIBRARY_PATH="${INTEL_HOME}/compiler/2022.2.1/linux/compiler/lib/intel64_lin:${LD_LIBRARY_PATH:-}"
export AIMS="/u/elsto/programs/FHIaims/build/aims.260326.scalapack.mpi.x"

ulimit -s unlimited

script_dir="${SLURM_SUBMIT_DIR:-$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)}"
readonly polarization_grids=(16 20 24 28 32 36 40 48 56 64 80)
cd "${script_dir}"

run_aims() {
    local output_file="$1"
    local temporary_output="aims.out"

    echo "Running ${output_file}"
    srun "${AIMS}" > "${temporary_output}" 2>&1
    cp "${temporary_output}" "${output_file}"
}

shopt -s nullglob
density_matrices=(D_spin_*.csc)
shopt -u nullglob
if (( ${#density_matrices[@]} == 0 )); then
    cp converge.in control.in
    run_aims results/aims.scf.out

    shopt -s nullglob
    density_matrices=(D_spin_*.csc)
    shopt -u nullglob
    if (( ${#density_matrices[@]} == 0 )); then
        echo "The reference SCF calculation did not create CSC restart files." >&2
        exit 1
    fi
fi

for n in "${polarization_grids[@]}"; do
    output_file="results/aims.n=${n}.out"
    if [[ -f "${output_file}" ]] && grep -q 'Have a nice day.' "${output_file}"; then
        echo "Keeping completed ${output_file}"
        continue
    fi
    sed "s/kkk/${n}/g" aims.in > control.in
    run_aims "${output_file}"
done
