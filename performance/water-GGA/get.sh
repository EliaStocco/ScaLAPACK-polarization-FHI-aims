for m in 128 196; do
    mkdir -p m=${m}
    mkdir -p m=${m}/dipole
    mkdir -p m=${m}/scf

    scp viper:/u/elsto/works/ScaLAPACK-performance/water/revPBE0/m=${m}/dipole-GGA/results/aims.*.out  m=${m}/dipole/.
    scp viper:/u/elsto/works/ScaLAPACK-performance/water/revPBE0/m=${m}/scf-GGA/results/aims.*.out  m=${m}/scf/.
done
