#!/bin/bash
for file in "$@"
do
    # Replace extension and leading subdirectories
    pyi_file="${file%.py}.pyi"

    # module level pyi file
    pyi_file="${pyi_file/#\/src\///tmp/pytype/pyi/}"

    # root level pyi file
    pyi_root="/tmp/pytype/pyi/$(basename "$pyi_file")"

    if [[ -f "$pyi_file" ]]; then
        merge-pyi -i "$file" "$pyi_file"
    elif [[ -f "$pyi_root" ]]; then
        merge-pyi -i "$file" "$pyi_root"
    else
        echo "Could not apply merge-pyi for {$file}"
    fi;
done
