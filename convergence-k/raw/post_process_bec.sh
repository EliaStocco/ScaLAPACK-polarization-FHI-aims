#!/usr/bin/env bash
# Compute fd2bec Born charges for every completed raw/bec_* k-grid calculation.
set -euo pipefail

script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"

if ! command -v post_process_aims > /dev/null; then
    echo "post_process_aims is unavailable. Activate the fd2bec environment first." >&2
    exit 1
fi

shopt -s nullglob
suites=("${script_dir}"/bec_*)
shopt -u nullglob
if (( ${#suites[@]} == 0 )); then
    echo "No raw/bec_* directories found next to ${BASH_SOURCE[0]}." >&2
    exit 1
fi

processed=0
for suite in "${suites[@]}"; do
    [[ -d "${suite}" ]] || continue
    shopt -s nullglob
    calculations=("${suite}"/k-grid-*)
    shopt -u nullglob
    for calculation in "${calculations[@]}"; do
        [[ -d "${calculation}" ]] || continue
        if [[ ! -f "${calculation}/DONE" ]]; then
            echo "Skipping ${calculation}: calculation is not marked DONE"
            continue
        fi
        if [[ ! -f "${calculation}/reference.extxyz" ]] || ! compgen -G "${calculation}/results/aims.n=*.out" > /dev/null; then
            echo "Skipping ${calculation}: reference structure or results are missing"
            continue
        fi
        echo "Computing Born charges for ${calculation#"${script_dir}"/}"
        (
            cd "${calculation}"
            post_process_aims \
                -i reference.extxyz \
                --results results \
                --dataset postprocess/dataset.extxyz \
                -o postprocess
        )
        ((processed += 1))
    done
done

if (( processed == 0 )); then
    echo "No completed k-grid calculations were processed." >&2
    exit 1
fi
echo "Computed Born charges for ${processed} k-grid calculation(s)."
