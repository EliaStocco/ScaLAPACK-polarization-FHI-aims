for m in 128 196; do
    mkdir -p m=${m}
    for xc in revPBE0 revPBE HSE06; do 
        mkdir -p m=${m}/xc=${xc}
        mkdir -p m=${m}/xc=${xc}/dipole
        mkdir -p m=${m}/xc=${xc}/scf
        for what in scf dipole; do
            scp viper:/u/elsto/works/ScaLAPACK-performance/water/new-m=${m}/${what}-${xc}/results/aims.*.out  m=${m}/xc=${xc}/${what}/.
        done
    done
done
