pyenv activate fd2bec
for xc in LDA PBE PBEsol; do
    cd ${xc}
    mkdir -p bec
    cd bec
    cp ../relax/final.extxyz start.extxyz
    cp ../../control.in .
    prepare_aims -i start.extxyz --k-grid 16 16 16 --k-grid-polarization 64 64 64
    cd ../..
done
