for folder in HSE06; do
    # HSE06
    cd "$folder" || continue

    # cd relax || continue
    # cp ../../main.sh .
    # JOB_ID=$(sbatch --parsable main.sh)
    # cd ..

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