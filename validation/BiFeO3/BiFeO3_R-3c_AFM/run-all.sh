#!/bin/bash
set -euo pipefail

for folder in LDA PBEsol HSE06; do
    cd "$folder" || continue

    cp relax/geometry.in converge/.
    cp relax/geometry.in lapack/.
    cp relax/geometry.in scalapack/.

    cd converge || continue
    JOB_ID=$(sbatch --parsable main.sh)
    cd ..

    cd lapack || continue
    submit.py -e "$JOB_ID"
    cd ..

    cd scalapack || continue
    submit.py -e "$JOB_ID"
    cd ..

    cd ..
done
