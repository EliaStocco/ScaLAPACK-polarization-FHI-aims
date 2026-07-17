pyenv activate fd2bec
for xc in LDA PBEsol HSE06; do
    sort_structure -r cubic/${xc}/geometry.in -i displaced/${xc}/geometry.in -o displaced/${xc}/geometry.in --atol 1
done
eslib
for xc in LDA PBEsol HSE06; do
    create-path-with-cell.py -a cubic/${xc}/geometry.in -b displaced/${xc}/geometry.in -n 8 -f true -o ${xc}.extxyz
done