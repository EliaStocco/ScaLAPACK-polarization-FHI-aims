#!/usr/bin/env bash
# Submit independent jobs: no failed run can block another core count.
set -euo pipefail

readonly campaign_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly partition=general
readonly constraint=largemem

submit_stage() {
  local size=$1 kind=$2 functional=$3 walltime=$4
  shift 4
  local cores nodes run_dir job_name job_id
  for cores in "$@"; do
    nodes=$(((cores + 127) / 128))
    run_dir="${campaign_dir}/${size}/${kind}-${functional}/n=${cores}"
    job_name="bto-${size}-${kind}-${functional}-n${cores}"
    job_id=$(cd "${run_dir}" && sbatch --parsable \
      --partition="${partition}" \
      --constraint="${constraint}" \
      --nodes="${nodes}" \
      --ntasks-per-node=128 \
      --time="${walltime}" \
      --job-name="${job_name}" \
      --output="slurm-%j.out" \
      --error="slurm-%j.err" \
      --export="ALL,RUN_CORES=${cores}" \
      "${campaign_dir}/run_aims.sh")
    printf '%-42s %s\n' "${job_name}" "${job_id}"
  done
}

# LDA is allotted up to 12 h. HSE06 receives the 24 h partition maximum,
# substantially longer than the original LDA allocations.
submit_stage 4x4x4 scf    LDA   12:00:00 128 256 512 768 900 1024 1080 2048
submit_stage 4x4x4 dipole LDA   12:00:00 128 256 512 768 900 1023 1080 2048
submit_stage 8x8x8 scf    LDA   12:00:00 1024 1152 1536 2048
submit_stage 8x8x8 dipole LDA   12:00:00 968 1024 1152 1536 1568 2048
submit_stage 4x4x4 scf    HSE06 24:00:00 128 256 512 768 900 1024 1080 2048
submit_stage 4x4x4 dipole HSE06 24:00:00 128 256 512 768 900 1023 1080 2048
submit_stage 8x8x8 scf    HSE06 24:00:00 1024 1152 1536 2048
submit_stage 8x8x8 dipole HSE06 24:00:00 968 1024 1152 1536 1568 2048
