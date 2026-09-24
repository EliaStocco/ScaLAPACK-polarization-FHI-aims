mkdir -p dipole
rsync -av --exclude='*.csc' viper:/ptmp/elsto/works/ScaLAPACK-comparison/2x2x2/dipole-2x2x16/ dipole/.
ln -s ../2x2x20/scf/ .