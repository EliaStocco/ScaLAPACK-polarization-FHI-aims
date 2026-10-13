#!/bin/bash -l
# Shared runner for one isolated core-count directory.
# The parent submit script supplies RUN_CORES. Each run directory is unique,
# so no job can overwrite another job's AIMS output.
#SBATCH --partition=general
#SBATCH --constraint=largemem
set -euo pipefail

: "${RUN_CORES:?RUN_CORES must be supplied by submit_all.sh}"
readonly AIMS_PATH=/u/elsto/programs/FHIaims-polarization-scalapack/build
readonly AIMS_EXE=aims.260527.scalapack.mpi.x
readonly result="aims.n=${RUN_CORES}.out"

if [[ -e "${result}" ]]; then
  printf 'Refusing to overwrite existing result: %s\n' "${PWD}/${result}" >&2
  exit 3
fi

module purge
module load intel/2024.0
module load impi/2021.11
module load mkl/2024.0
export LD_LIBRARY_PATH="${MKL_HOME}/lib/intel64:${LD_LIBRARY_PATH:-}"
export LD_LIBRARY_PATH="${INTEL_HOME}/compiler/2022.2.1/linux/compiler/lib/intel64_lin:${LD_LIBRARY_PATH}"
ulimit -s unlimited

printf '# Start: %s\n# MPI ranks: %s\n' "$(date '+%F %T')" "${RUN_CORES}" > job.log
srun -n "${RUN_CORES}" "${AIMS_PATH}/${AIMS_EXE}" > "${result}" 2>&1
printf '# End: %s\n' "$(date '+%F %T')" >> job.log
