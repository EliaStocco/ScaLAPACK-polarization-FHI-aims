generate_all_displacements -i start.extxyz -o all_minus_displacements.txt  -a -0.001
generate_all_displacements -i start.extxyz -o all_plus_displacements.txt   -a 0.001
cat null.txt all_plus_displacements.txt all_minus_displacements.txt > all_displacements.txt
apply_displacements -i start.extxyz -d all_displacements.txt -o displaced.extxyz
# convert-file.py -i displaced.extxyz -o geometry.in -f geometries

