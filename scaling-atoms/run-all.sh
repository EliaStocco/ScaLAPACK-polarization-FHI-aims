#!/bin/bash

supercells=(
    "1x1x1"
    "2x1x1"
    "2x2x1"
    "2x2x2"
    "4x2x2"
    "4x4x2"
    "4x4x4"
    "8x4x4"
    "8x8x4"
    "8x8x8"
)

for supercell in "${supercells[@]}"; do
    echo "Submitting supercell-${supercell}"

    cd "supercell-${supercell}" || exit 1

    # 8x8x8: skip convergence and SCF calculations.
    # Submit only the LAPACK and ScaLAPACK dipole calculations.
    if [[ "${supercell}" == "8x8x8" ]]; then
        (
            cd lapack/dipole || exit 1
            sbatch main.sh
        )

        (
            cd scalapack/dipole || exit 1
            sbatch main.sh
        )

        cd ..
        continue
    fi

    # Submit convergence calculation first.
    cd converge || exit 1
    converge_job=$(sbatch main.sh)
    converge_id=$(echo "${converge_job}" | awk '{print $4}')
    cd ..

    echo "Convergence job ID: ${converge_id}"

    # LAPACK
    if [[ -d lapack/scf ]]; then
        (
            cd lapack/scf || exit 1
            sbatch --dependency=afterok:${converge_id} main.sh
        )
    fi

    if [[ -d lapack/dipole ]]; then
        (
            cd lapack/dipole || exit 1
            sbatch --dependency=afterok:${converge_id} main.sh
        )
    fi

    # ScaLAPACK
    if [[ -d scalapack/scf ]]; then
        (
            cd scalapack/scf || exit 1
            sbatch --dependency=afterok:${converge_id} main.sh
        )
    fi

    if [[ -d scalapack/dipole ]]; then
        (
            cd scalapack/dipole || exit 1
            sbatch --dependency=afterok:${converge_id} main.sh
        )
    fi

    cd ..
done