#!/bin/bash

for n in 1 2 3 4 6 7 8; do
    dir="supercell-${n}"
    
    if [ ! -d "$dir" ]; then
        echo "Directory $dir does not exist, skipping..."
        continue
    fi

    (
        cd "$dir" || exit 1
        
        # 1. Submit main convergence job and capture Slurm Job ID
        if [ -d "converge" ]; then
            JOB_ID=$(cd converge && sbatch --parsable main.sh)
            echo "Submitted converge job for $dir: $JOB_ID"
        fi

        # 2. LAPACK jobs (dependent on main job finishing)
        if [ -d "lapack" ]; then
            (
                cd lapack || exit 1
                [ -d "dipole" ] && (cd dipole && submit.py -e "${JOB_ID}")
                [ -d "scf" ]    && (cd scf    && submit.py -e "${JOB_ID}")
            )
        fi

        # 3. ScaLAPACK jobs (dependent on main job finishing)
        if [ -d "scalapack" ]; then
            (
                cd scalapack || exit 1
                [ -d "dipole" ] && (cd dipole && submit.py -e "${JOB_ID}")
                [ -d "scf" ]    && (cd scf    && submit.py -e "${JOB_ID}")
            )
        fi
    )
done
