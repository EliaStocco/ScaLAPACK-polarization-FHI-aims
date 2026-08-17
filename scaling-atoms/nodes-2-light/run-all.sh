#!/bin/bash

# Resolve paths from this file so the script can be sourced from any directory.
_nodes_2_light_root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)

_submit_nodes_2_light_jobs() {
    local n dir job_id calculation
    local status=0

    for n in 1 2 3 4 6 7 8; do
        dir="${_nodes_2_light_root}/supercell-${n}"

        if [ ! -d "$dir" ]; then
            echo "Directory $dir does not exist, skipping..." >&2
            status=1
            continue
        fi

        if [ ! -d "$dir/converge" ]; then
            echo "Missing convergence directory: $dir/converge" >&2
            status=1
            continue
        fi

        if ! job_id=$(cd "$dir/converge" && sbatch --parsable main.sh); then
            echo "Failed to submit convergence job for supercell-${n}" >&2
            status=1
            continue
        fi
        echo "Submitted converge job for supercell-${n}: $job_id"

        # Submit every calculation present in the LAPACK and ScaLAPACK trees.
        # submit.py makes each one depend on the corresponding convergence job.
        for calculation in \
            lapack/dipole lapack/scf \
            scalapack/dipole scalapack/scf; do
            [ -d "$dir/$calculation" ] || continue
            if ! (cd "$dir/$calculation" && submit.py -e "$job_id"); then
                echo "Failed to submit supercell-${n}/$calculation" >&2
                status=1
            fi
        done
    done

    return "$status"
}

_submit_nodes_2_light_jobs
_nodes_2_light_status=$?
unset -f _submit_nodes_2_light_jobs
unset _nodes_2_light_root

# Work both when sourced (recommended) and when executed directly.
if [ "$_nodes_2_light_status" -eq 0 ]; then
    unset _nodes_2_light_status
    return 0 2>/dev/null || exit 0
else
    unset _nodes_2_light_status
    return 1 2>/dev/null || exit 1
fi
