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
cd validation
find . -type d -name "converge" -exec rm -rf {} +
find . -type d -name "slurm" -exec rm -rf {} +
find . -type f -name "aims.in" -delete
find . -type f -name "log.out" -delete
find . -type f -name "species.tight.in" -delete
cd ..