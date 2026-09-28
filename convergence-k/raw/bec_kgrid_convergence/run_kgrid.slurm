#!/bin/bash -l
#SBATCH -o slurm/output.txt
#SBATCH -e slurm/error.txt
#SBATCH -J bec-1x1x1
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=72
#SBATCH --mail-type=NONE
#SBATCH --time=04:00:00

set -euo pipefail

module purge
module load intel/2024.0
module load impi/2021.11
module load mkl/2024.0
export LD_LIBRARY_PATH="${MKL_HOME}/lib/intel64:${LD_LIBRARY_PATH:-}"
export LD_LIBRARY_PATH="${INTEL_HOME}/compiler/2022.2.1/linux/compiler/lib/intel64_lin:${LD_LIBRARY_PATH:-}"
export AIMS="/u/elsto/programs/FHIaims/build/aims.260326.scalapack.mpi.x"

ulimit -s unlimited
# Slurm executes a spool copy of this file, so BASH_SOURCE points to
# /var/spool/slurmd rather than the calculation directory. The submitter
# sets each job's working directory to its k-grid directory.
calculation_dir="$(pwd -P)"
script_dir="$(cd -- "${calculation_dir}/.." && pwd -P)"
"${script_dir}/run_kgrid.sh" "${calculation_dir}"
