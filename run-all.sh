cd validation
mkdir -p data
python scripts/check-files.py  -i dataframe.csv 
python scripts/extract-data.py -i dataframe.csv -o data/dataframe.csv
cd -