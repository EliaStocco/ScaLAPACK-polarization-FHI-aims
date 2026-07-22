#!/bin/bash
set -euo pipefail

for structure in BiFeO3_R-3c_AFM BiFeO3_R3c_AFM; do
    cd "$structure" || continue
    ./run-all.sh
    cd ..
done
