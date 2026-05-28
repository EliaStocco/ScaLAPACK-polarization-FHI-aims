#!/bin/bash -l
# Standard output and error:
#SBATCH -o slurm/output.txt
#SBATCH -e slurm/error.txt
# Initial working directory:
#SBATCH -D ./
# Job Name:
#SBATCH -J BaTiO3

#SBATCH --nodes=1
#SBATCH --ntasks-per-node=128
#SBATCH --mail-type=NONE
#SBATCH --time=00:10:00

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
# conda activate eslib
# source ~/programs/eslib/install.sh
export LD_LIBRARY_PATH="${MKL_HOME}/lib/intel64:${LD_LIBRARY_PATH}"
export LD_LIBRARY_PATH="${INTEL_HOME}/compiler/2022.2.1/linux/compiler/lib/intel64_lin:${LD_LIBRARY_PATH}"

# Programs and paths
PROGRAMS_DIR="/u/elsto/programs"
export AIMS_PATH="${PROGRAMS_DIR}/FHIaims-polarization-scalapack/build"
export AIMS_EXE="aims.260331.scalapack.mpi.x"

ulimit -s unlimited

#-----------------------------------#
# Functions
get_current_date_time() {
    date +"%Y-%m-%d %H:%M:%S"
}

calculate_elapsed_time() {
    start_time="$1"
    end_time="$2"
    start_seconds=$(date -d "$start_time" +%s)
    end_seconds=$(date -d "$end_time" +%s)
    elapsed_seconds=$((end_seconds - start_seconds))
    echo "$elapsed_seconds seconds"
}

run_aims(){
    echo "Running ${AIMS_OUTPUT_FILE}" >> "$LOG_FILE"
    start_time=$(get_current_date_time)
    cmd="srun ${AIMS_PATH}/${AIMS_EXE} &> aims.out"
    echo "$cmd"
    eval "$cmd"
    end_time=$(get_current_date_time)
    echo "# End Time: $end_time" >> "$LOG_FILE"
    echo "# Elapsed Time: $(calculate_elapsed_time "$start_time" "$end_time")" >> "$LOG_FILE"
    echo ""
    cp aims.out ${AIMS_OUTPUT_FILE}
}

#-----------------------------------#
# Logging
LOG_FILE="log.out"
rm -f "$LOG_FILE"
echo "# Job ID: $SLURM_JOB_ID" >> "$LOG_FILE"
echo "# Date and Time: $(date +"%Y-%m-%d %H:%M:%S")" >> "$LOG_FILE"

# optimize.py  -i geometry.in -rc true -f 0.0001 -u false -a localhost -p 10200 & 
# sleep 10

AIMS_OUTPUT_FILE="scf.out"
cat aims.in species.tight.in > control.in
run_aims

