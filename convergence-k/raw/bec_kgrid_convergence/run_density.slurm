#!/bin/bash -l
#SBATCH -o slurm/density-output.txt
#SBATCH -e slurm/density-error.txt
#SBATCH -D ./
#SBATCH -J bec-density-1x1x1
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=72
#SBATCH --mail-type=NONE
#SBATCH --time=04:00:00

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
./run_density.sh
