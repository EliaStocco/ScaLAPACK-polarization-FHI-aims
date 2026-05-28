rm -rf validation/BaTiO3/cubic/*/*/results/
rm -rf validation/BaTiO3/rhombohedral/*/*/results/
find . -type f -name "scf.out" | while read -r scf; do
    dir=$(dirname "$scf")
    aims="$dir/aims.out"

    if [ -f "$aims" ] && cmp -s "$scf" "$aims"; then
        echo "Removing identical file: $scf"
        rm "$scf"
    fi
done