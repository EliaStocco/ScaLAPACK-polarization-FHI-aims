#!/bin/bash -l
#SBATCH -o slurm/output.txt
#SBATCH -e slurm/error.txt
#SBATCH -D ./
#SBATCH -J bec-1x1x1
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=72
#SBATCH --mail-type=NONE
#SBATCH --time=24:00:00

set -euo pipefail

mkdir -p slurm
module purge
module load intel/2024.0
module load impi/2021.11
module load mkl/2024.0
export LD_LIBRARY_PATH="${MKL_HOME}/lib/intel64:${LD_LIBRARY_PATH:-}"
export LD_LIBRARY_PATH="${INTEL_HOME}/compiler/2022.2.1/linux/compiler/lib/intel64_lin:${LD_LIBRARY_PATH:-}"
export AIMS="/u/elsto/programs/FHIaims/build/aims.260326.scalapack.mpi.x"

ulimit -s unlimited

# Run every prepared k-grid sequentially in this allocation.
script_dir="${SLURM_SUBMIT_DIR:-$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)}"
for calculation_dir in "${script_dir}"/k-grid-*; do
    [[ -f "${calculation_dir}/sourceme.sh" ]] || continue
    echo "Running ${calculation_dir##*/}"
    "${script_dir}/run_kgrid.sh" "${calculation_dir}"
done
