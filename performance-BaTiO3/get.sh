for s in 4; do
    mkdir -p ${s}x${s}x${s}
    mkdir -p ${s}x${s}x${s}/dipole
    mkdir -p ${s}x${s}x${s}/scf

    scp viper:/u/elsto/works/ScaLAPACK-performance/BaTiO3/time-vs-cores/${s}x${s}x${s}/dipole-bis/results/aims.*.out  ${s}x${s}x${s}/dipole/.
    scp viper:/u/elsto/works/ScaLAPACK-performance/BaTiO3/time-vs-cores/${s}x${s}x${s}/scf/results/aims.*.out  ${s}x${s}x${s}/scf/.
done

for s in 8; do
    mkdir -p ${s}x${s}x${s}
    mkdir -p ${s}x${s}x${s}/dipole
    mkdir -p ${s}x${s}x${s}/scf

    scp viper:/u/elsto/works/ScaLAPACK-performance/BaTiO3/time-vs-cores/${s}x${s}x${s}/dipole/results/aims.*.out  ${s}x${s}x${s}/dipole/.
    scp viper:/u/elsto/works/ScaLAPACK-performance/BaTiO3/time-vs-cores/${s}x${s}x${s}/scf/results/aims.*.out  ${s}x${s}x${s}/scf/.
done
