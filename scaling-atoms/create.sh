make-supercell.py -i supercell-1x1x1/geometry.in -o supercell-2x1x1/geometry.in -m "2 1 1"
make-supercell.py -i supercell-1x1x1/geometry.in -o supercell-2x2x1/geometry.in -m "2 2 1"

make-supercell.py -i supercell-1x1x1/geometry.in -o supercell-4x2x2/geometry.in -m "4 2 2"
make-supercell.py -i supercell-1x1x1/geometry.in -o supercell-4x4x2/geometry.in -m "4 4 2"

make-supercell.py -i supercell-1x1x1/geometry.in -o supercell-8x4x4/geometry.in -m "8 4 4"
make-supercell.py -i supercell-1x1x1/geometry.in -o supercell-8x8x4/geometry.in -m "8 8 4"

for folder in supercell-2x1x1 supercell-2x2x1 supercell-4x2x2 supercell-4x4x2 supercell-8x4x4 supercell-8x8x4 ; do
    cd ${folder}
    python ../frac.py
    cd -
done