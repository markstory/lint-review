#!/bin/bash
# Installer script for the various golang
# package managers.
installer="$1"

cd /src || exit 1

if [[ $installer == "dep" ]]
then
	dep ensure
elif [[ $installer == "govendor" ]]
then
	govendor install +local
elif [[ $installer == "mod" ]]
then
	go get ./...
else
	echo "Could not install dependencies."
	exit 1
fi
