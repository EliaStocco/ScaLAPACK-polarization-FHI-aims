#!/bin/bash

# Exit on errors
set -e

# Find all directories containing aims.out (unique)
find . -type f -name "aims.out" -exec dirname {} \; | sort -u | while read -r dir; do

    subfolder=$(realpath --relative-to=. "$dir")

    # echo "Processing: $subfolder"

    # Add folder
    git add "$subfolder"

    # Commit only if there are staged changes
    if git diff --cached --quiet; then
        # echo "No changes in $subfolder, skipping commit"
        continue
    fi

    git commit -m "Add results for ${subfolder}"

    git push origin master

done
