#!/bin/sh

cd /tool || exit 1

# Install packages in $1 (comma separated) with pip
for i in $(echo "$1" | sed "s/,/ /g")
do
    pip install "$i"
done
