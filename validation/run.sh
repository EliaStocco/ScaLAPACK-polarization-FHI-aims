python3 scripts/extract_polarization.py BaTiO3 --structures cubic rhombohedral --output BaTiO3.csv  > BaTiO3.txt
python3 scripts/extract_polarization.py BaTiO3 --structures cubic tetragonal --output BaTiO3-t.csv  > BaTiO3-t.txt
# python3 scripts/extract_polarization.py PbTiO3 --structures cubic displaced --output PbTiO3.csv  > PbTiO3.txt
python3 test-PbTiO3/extract_folded_polarization.py --pbe-endpoint-branch-shifts 0 0 1 > PbTiO3.txt
# python3 scripts/extract_polarization.py BiFeO3 --structures BiFeO3_R-3c_AFM BiFeO3_R3c_AFM --output BiFeO3.csv  > BiFeO3.txt
python3 BiFeO3/extract_polarization_difference.py --method scalapack > BiFeO3.txt
