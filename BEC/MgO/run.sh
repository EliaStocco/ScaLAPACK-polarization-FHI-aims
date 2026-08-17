pyenv activate fd2bec
for folder in LDA PBE PBEsol; do
    cd ${folder}/bec
    post_process_aims -i start.extxyz
    cd ../..
done