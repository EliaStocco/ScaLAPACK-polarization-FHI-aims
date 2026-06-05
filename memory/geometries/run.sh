for n in {1..12}; do
    make-supercell.py -i geometry.in -o geometry.${n}x${n}x${n}.in -m "${n} ${n} ${n}"
done