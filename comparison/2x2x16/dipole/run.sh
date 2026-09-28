#!/bin/bash

pairs=(
    "1 10"
    "1 12"
    "1 14"
    "1 20"
    "1 24"
    "1 28"
    "1 40"
    "1 48"
    "1 56"
    #"1 8"
    #"1 16"
    #"1 32"
    #"1 64"
    #"1 128"
    #"2 256"
    #"4 512"
    #"8 1024"
)

for pair in "${pairs[@]}"; do
    read -r NNODES NUM_CORES <<< "$pair"

    sed \
        -e "s/NNODES/${NNODES}/g" \
        -e "s/NUM_CORES/${NUM_CORES}/g" \
        template.sh | sbatch

    echo "Submitted: nodes=$NNODES cores=$NUM_CORES"
done
