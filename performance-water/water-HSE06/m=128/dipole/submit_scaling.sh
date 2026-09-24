#!/usr/bin/env bash
# Submit main.sh serially at increasing node counts.  Each job starts only
# after the preceding one completes successfully.
set -euo pipefail

submit_job() {
    local nodes=$1
    local dependency=${2:-}
    local args=(--parsable --nodes="$nodes" --job-name="water-n${nodes}")

    if [[ -n $dependency ]]; then
        args+=(--dependency="afterok:${dependency}")
    fi

    sbatch "${args[@]}" main.sh
}

job_1=$(submit_job 1)
job_2=$(submit_job 2 "$job_1")
job_4=$(submit_job 4 "$job_2")
job_8=$(submit_job 8 "$job_4")

printf 'Submitted jobs:\n'
printf '  1 node: %s\n' "$job_1"
printf '  2 nodes: %s (afterok:%s)\n' "$job_2" "$job_1"
printf '  4 nodes: %s (afterok:%s)\n' "$job_4" "$job_2"
printf '  8 nodes: %s (afterok:%s)\n' "$job_8" "$job_4"
