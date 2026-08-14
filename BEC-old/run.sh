set-cell.py -i BaTiO3.cif -o BaTiO3-LDA/start.extxyz -abc [3.958,3.958,3.958]
set-cell.py -i BaTiO3.cif -o BaTiO3-PBE/start.extxyz -abc [4.035,4.035,4.035]

set-cell.py -i MgO.cif -o MgO-LDA/start.extxyz -abc [4.240,4.240,4.240]
set-cell.py -i MgO.cif -o MgO-PBE/start.extxyz -abc [4.283,4.283,4.283]

for folder in BaTiO3-LDA BaTiO3-PBE MgO-LDA MgO-PBE; do
    cd ${folder}
    information-and-primitive.py -i start.extxyz -sp true > summary.txt
    cd ..
done

pyenv activate fd2bec

for folder in BaTiO3-LDA BaTiO3-PBE MgO-LDA MgO-PBE; do
    cd ${folder}
    prepare_aims -i start.extxyz
    cd ..
done

for folder in BaTiO3-LDA BaTiO3-PBE MgO-LDA MgO-PBE; do
    cd ${folder}
    post_process_aims -i start.extxyz
    cd ..
done