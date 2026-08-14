#!/bin/bash -l
# Standard output and error:
#SBATCH -o slurm/output.txt
#SBATCH -e slurm/error.txt
# Initial working directory:
#SBATCH -D ./
# Job Name:
#SBATCH -J BaTiO3-BEC

#SBATCH --nodes=1
#SBATCH --ntasks-per-node=128
#SBATCH --mail-type=NONE
#SBATCH --time=01:00:00

###################################################################
# Clean slurm folder
rm -rf slurm/*
mkdir -p slurm
exec >> slurm/my_output.txt 2>&1   # Optional: redirect all output

# Load modules
module purge
module load intel/2024.0 
module load impi/2021.11 
module load mkl/2024.0
export LD_LIBRARY_PATH="${MKL_HOME}/lib/intel64:${LD_LIBRARY_PATH}"
export LD_LIBRARY_PATH="${INTEL_HOME}/compiler/2022.2.1/linux/compiler/lib/intel64_lin:${LD_LIBRARY_PATH}"

# Programs and paths
PROGRAMS_DIR="/u/elsto/programs"
export AIMS_PATH="${PROGRAMS_DIR}/FHIaims-polarization-scalapack/build/"
export AIMS_EXE="aims.260527.scalapack.mpi.x"

export AIMS="${AIMS_PATH}/${AIMS_EXE}"
source sourceme.sh