import os
import pandas as pd
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("-i", "--input" , type=str, required=True, help="input CSV file.")
args = parser.parse_args()

df = pd.read_csv(args.input)

for n,row in df.iterrows():
    if pd.isna(row['file']):
        continue
    if not os.path.exists(row['file']):
        print(f"File '{row['file']}' does not exist.")