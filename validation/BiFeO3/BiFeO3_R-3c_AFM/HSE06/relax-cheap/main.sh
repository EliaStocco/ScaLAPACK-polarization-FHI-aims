#!/bin/bash -l
# Standard output and error:
#SBATCH -o slurm/output.txt
#SBATCH -e slurm/error.txt
# Initial working directory:
#SBATCH -D ./
# Job Name:
#SBATCH -J BiFeO3-AFM

#SBATCH --nodes=4
#SBATCH --ntasks-per-node=128
#SBATCH --mail-type=NONE
#SBATCH --time=04:00:00

###################################################################
# Logging and error handling
set -Eeuo pipefail

mkdir -p slurm

JOB_ID="${SLURM_JOB_ID:-manual-$$}"
LOG_FILE="log.out"
DETAIL_LOG="slurm/my_output-${JOB_ID}.txt"
TRACE_LOG="slurm/shell-trace-${JOB_ID}.txt"
SECONDS=0

# Keep stdout and stderr in the requested Slurm files while also retaining a
# combined, job-specific copy. Do not remove slurm/* here: Slurm has already
# opened output.txt and error.txt before the script starts.
exec > >(tee -a "$DETAIL_LOG") 2> >(tee -a "$DETAIL_LOG" >&2)

rm -f "$LOG_FILE"

log() {
    printf '[%(%Y-%m-%d %H:%M:%S)T] %s\n' -1 "$*" | tee -a "$LOG_FILE"
}

optimizer_pid=""

on_error() {
    local rc=$?
    log "ERROR: exit=$rc line=${BASH_LINENO[0]} command=${BASH_COMMAND}"
    return "$rc"
}

on_exit() {
    local rc=$?
    set +x
    trap - ERR

    if [[ -n "$optimizer_pid" ]] && kill -0 "$optimizer_pid" 2>/dev/null; then
        log "Stopping optimizer process PID=$optimizer_pid"
        kill "$optimizer_pid" 2>/dev/null || true
        wait "$optimizer_pid" 2>/dev/null || true
    fi

    log "Job finished: exit=$rc elapsed=${SECONDS}s"
}

trap on_error ERR
trap on_exit EXIT
trap 'exit 143' TERM
trap 'exit 130' INT

log "Job started"
log "Job ID: $JOB_ID"
log "Working directory: $PWD"
log "Host: $(hostname)"
log "Node list: ${SLURM_JOB_NODELIST:-not-running-under-slurm}"
log "Tasks: ${SLURM_NTASKS:-unknown}"
log "CPUs per task: ${SLURM_CPUS_PER_TASK:-unknown}"
log "Submission host: ${SLURM_SUBMIT_HOST:-unknown}"

# Load modules
log "Loading software environment"
module purge
module load intel/2024.0
module load impi/2021.11
module load mkl/2024.0
export PYTHONPATH="${PYTHONPATH:-}:/u/elsto/programs/eslib"
conda activate eslib
source ~/programs/eslib/install.sh
export LD_LIBRARY_PATH="${MKL_HOME}/lib/intel64:${LD_LIBRARY_PATH:-}"
export LD_LIBRARY_PATH="${INTEL_HOME}/compiler/2022.2.1/linux/compiler/lib/intel64_lin:${LD_LIBRARY_PATH}"

# Programs and paths
export AIMS_PATH="/u/elsto/programs/FHIaims-polarization-scalapack/build"
export AIMS_EXE="aims.260527.scalapack.mpi.x"

ulimit -s unlimited

log "Python: $(command -v python || printf 'not found')"
log "Python version: $(python --version 2>&1 || printf 'unavailable')"
log "Optimizer: $(command -v optimize.py || printf 'not found')"
log "Trajectory converter: $(command -v tra2extxyz.py || printf 'not found')"
log "FHI-aims executable: ${AIMS_PATH}/${AIMS_EXE}"
log "Stack limit: $(ulimit -s)"
log "Loaded modules:"
module list 2>&1 | tee -a "$LOG_FILE" || true

# Record every subsequent shell command in a separate trace without flooding
# the primary job output with module/Conda initialization internals.
exec 19>>"$TRACE_LOG"
export BASH_XTRACEFD=19
export PS4='+ ${EPOCHREALTIME} ${BASH_SOURCE}:${LINENO}: '
set -x

run_aims() {
    local output_file="$1"
    local start_time=$SECONDS
    local rc

    log "Starting FHI-aims: output=$output_file"
    log "Command: srun ${AIMS_PATH}/${AIMS_EXE}"

    if srun "${AIMS_PATH}/${AIMS_EXE}" >"$output_file" 2>&1; then
        rc=0
    else
        rc=$?
    fi

    log "FHI-aims process ended: output=$output_file exit=$rc elapsed=$((SECONDS-start_time))s"
    if [[ -f "$output_file" ]]; then
        log "FHI-aims output size: $(wc -c < "$output_file") bytes, $(wc -l < "$output_file") lines"
    fi

    if (( rc != 0 )); then
        log "FHI-aims/srun failed; last 50 output lines follow"
        tail -n 50 "$output_file" | tee -a "$LOG_FILE"
        return "$rc"
    fi

    # Some FHI-aims fatal errors still result in a zero srun exit status.
    if ! grep -q "Have a nice day" "$output_file"; then
        log "FHI-aims did not reach its normal-termination marker"
        tail -n 50 "$output_file" | tee -a "$LOG_FILE"
        return 1
    fi

    log "FHI-aims completed normally: output=$output_file"
}

prepare_restart_geometry() {
    local trajectory_file="minimization-trajectory.traj"
    local trajectory_extxyz="minimization-trajectory.extxyz"

    if [[ ! -s "$trajectory_file" ]]; then
        log "No non-empty $trajectory_file found; using the submitted geometry.in"
        return 0
    fi

    if ! command -v tra2extxyz.py >/dev/null 2>&1; then
        log "Cannot restart: tra2extxyz.py is not available after loading eslib"
        return 127
    fi

    log "Restarting from $trajectory_file ($(wc -c < "$trajectory_file") bytes)"
    log "Command: tra2extxyz.py $trajectory_file $trajectory_extxyz"
    tra2extxyz.py "$trajectory_file" "$trajectory_extxyz" 2>&1 | tee -a "$LOG_FILE"

    if [[ ! -s "$trajectory_extxyz" ]]; then
        log "Trajectory conversion produced no non-empty $trajectory_extxyz"
        return 1
    fi

    log "Command: convert-file.py -i $trajectory_extxyz -o geometry.in --index -1"
    convert-file.py -i "$trajectory_extxyz" -o geometry.in --index -1 2>&1 | tee -a "$LOG_FILE"
    log "Restart geometry generated from the final trajectory snapshot"
}

#-----------------------------------#
prepare_restart_geometry

log "Saving the starting geometry as original.in"
cp geometry.in original.in

export SOCKET_HOST="${SOCKET_HOST:-$(hostname -i | awk '{print $1}')}"
export SOCKET_PORT=$((1025 + RANDOM % (65535 - 1025 + 1)))
log "Optimizer socket: ${SOCKET_HOST}:${SOCKET_PORT}"

log "Starting optimizer; stdout and stderr will be written to optimize.txt"
PYTHONUNBUFFERED=1 optimize.py -i geometry.in -p "${SOCKET_PORT}" -f 1e-4 -cs true -rc true --print-cell true > optimize.txt 2>&1 &
optimizer_pid=$!
log "Optimizer started: PID=$optimizer_pid"

echo "use_pimd_wrapper ${SOCKET_HOST} ${SOCKET_PORT}" > tmp.in

cat tmp.in aims.in > control.in
rm tmp.in

log "Waiting 10 seconds for the optimizer socket"
sleep 10

if ! kill -0 "$optimizer_pid" 2>/dev/null; then
    if wait "$optimizer_pid"; then
        optimizer_rc=0
    else
        optimizer_rc=$?
    fi
    optimizer_pid=""
    log "Optimizer exited before FHI-aims started: exit=$optimizer_rc"
    tail -n 50 optimize.txt | tee -a "$LOG_FILE"
    exit 1
fi

run_aims "scf.out"

log "Waiting for optimizer PID=$optimizer_pid"
if wait "$optimizer_pid"; then
    optimizer_rc=0
else
    optimizer_rc=$?
fi
optimizer_pid=""
log "Optimizer ended: exit=$optimizer_rc"

if (( optimizer_rc != 0 )); then
    log "Optimizer failed; last 50 output lines follow"
    tail -n 50 optimize.txt | tee -a "$LOG_FILE"
    exit "$optimizer_rc"
fi

if [[ ! -s final.extxyz ]]; then
    log "Optimizer produced no non-empty final.extxyz"
    exit 1
fi

log "Optimizer completed and produced final.extxyz ($(wc -c < final.extxyz) bytes)"

rm -f minimization-trajectory.pickle
rm -f minimization-trajectory.extxyz

#-----------------------------------#

log "Converting final.extxyz to geometry.in"
convert-file.py -i final.extxyz -o geometry.in

log "Computing symmetry information"
information-and-primitive.py -i geometry.in > symmetry.txt

log "Preparing final FHI-aims calculation"
cp aims.in control.in
run_aims "relax.out"
