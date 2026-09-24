#!/usr/bin/env bash
# Submit one fully occupied largemem-node job at each requested scale.
# Jobs run serially because they share this working directory.
set -euo pipefail

submit_job() {
    local nodes=$1
    local dependency=${2:-}
    local args=(--parsable --nodes="$nodes" --ntasks-per-node=128 --job-name="water-dipole-HSE06-n${nodes}")

    if [[ -n $dependency ]]; then
        args+=(--dependency="afterok:${dependency}")
    fi

    sbatch "${args[@]}" main.sh
}

job_2=$(submit_job 2)
job_4=$(submit_job 4 "$job_2")
job_8=$(submit_job 8 "$job_4")
job_16=$(submit_job 16 "$job_8")
