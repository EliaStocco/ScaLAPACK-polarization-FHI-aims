#!/bin/bash -l
set -euo pipefail

module purge
module load intel/2024.0
module load impi/2021.11
module load mkl/2024.0
export LD_LIBRARY_PATH="${MKL_HOME}/lib/intel64:${LD_LIBRARY_PATH}"
export LD_LIBRARY_PATH="${INTEL_HOME}/compiler/2022.2.1/linux/compiler/lib/intel64_lin:${LD_LIBRARY_PATH}"
ulimit -s unlimited

mkdir -p results
{
    echo "# Job ID: ${SLURM_JOB_ID}"
    echo "# Start time: $(date '+%Y-%m-%d %H:%M:%S')"
    echo "# Cores: ${NUM_CORES}"
    echo "# Executable: ${AIMS_EXE}"
    sha256sum "${AIMS_EXE}"
} > log.out

start_seconds=$(date +%s)
srun -n "${NUM_CORES}" "${AIMS_EXE}" > "results/aims.n=${NUM_CORES}.out" 2>&1
end_seconds=$(date +%s)

{
    echo "# End time: $(date '+%Y-%m-%d %H:%M:%S')"
    echo "# Elapsed time: $((end_seconds - start_seconds)) seconds"
} >> log.out
