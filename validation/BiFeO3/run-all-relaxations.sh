#!/bin/bash
set -euo pipefail

# Submit every BiFeO3 relaxation job:
# - 2 structures
# - 3 functionals each

structures=(
  "BiFeO3_R-3c_AFM"
  "BiFeO3_R3c_AFM"
)

functionals=(
  "LDA"
  "PBEsol"
  "HSE06"
)

for structure in "${structures[@]}"; do
  for functional in "${functionals[@]}"; do
    relax_dir="${structure}/${functional}/relax"
    if [[ ! -d "${relax_dir}" ]]; then
      echo "Missing relax directory: ${relax_dir}" >&2
      exit 1
    fi

    job_id="$(
      cd "${relax_dir}" && sbatch --parsable main.sh
    )"

    echo "Submitted ${relax_dir} -> ${job_id}"
  done
done
