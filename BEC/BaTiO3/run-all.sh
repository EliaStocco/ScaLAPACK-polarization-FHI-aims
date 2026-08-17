for xc in LDA PBE PBEsol; do
    cd ${xc}/bec
    cp ../../main.sh .
    sbatch main.sh
    cd ../..
done
