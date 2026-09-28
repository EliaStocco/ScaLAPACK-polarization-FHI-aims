#!/usr/bin/env bash
# Compatibility entry point for the repository-wide fd2bec post-processing.
script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
exec "${script_dir}/../post_process_bec.sh" "$@"
