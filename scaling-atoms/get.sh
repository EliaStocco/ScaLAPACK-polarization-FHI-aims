#!/usr/bin/env bash

set -euo pipefail

script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
rsync -av --exclude='*.csc' \
    viper:/u/elsto/works/ScaLAPACK-atoms-k-grid/ "${script_dir}/"
