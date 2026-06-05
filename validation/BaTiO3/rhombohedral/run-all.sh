for folder in PBEsol PBEsol-spin LDA HSE06; do
    cd "$folder" || continue

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