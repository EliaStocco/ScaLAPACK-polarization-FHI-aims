#!/bin/bash -l
# Standard output and error:
#SBATCH -o slurm/output.txt
#SBATCH -e slurm/error.txt
# Initial working directory:
#SBATCH -D ./
# Job Name:
#SBATCH -J BEC

#SBATCH --nodes=1
#SBATCH --ntasks-per-node=72
#SBATCH --mail-type=NONE
#SBATCH --time=02:00:00

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
export AIMS_EXE="/u/elsto/programs/FHIaims/build/aims.260326.scalapack.mpi.x"
source sourceme.sh