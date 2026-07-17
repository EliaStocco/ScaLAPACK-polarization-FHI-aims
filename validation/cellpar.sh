for folder in cubic rhombohedral; do
    for xc in PBEsol LDA; do
        printf "%-15s %-15s %s\n" \
            "BaTiO3" "$folder" "$xc $(grep "(a, b, c, α, β, γ)" "BaTiO3/${folder}/${xc}/relax/symmetry.txt")"
    done
done

for folder in cubic displaced; do
    for xc in PBEsol LDA; do
        printf "%-15s %-15s %s\n" \
            "PbTiO3" "$folder" "$xc $(grep "(a, b, c, α, β, γ)" "PbTiO3/${folder}/${xc}/relax/symmetry.txt")"
    done
done