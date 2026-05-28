find . -type f -name "aims.out" | while read -r aims; do
    dir=$(dirname "$aims")
    subfolder=$(realpath --relative-to=. "$dir")

    git add "$subfolder"
    git commit -m "added ${subfolder}"
    git push origin master
done