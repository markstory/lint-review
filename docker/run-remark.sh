#!/bin/bash

# Remark-CLI requires that it be run with `node_modules`
# relative to the source being processed so that presets
# and lint rule modules can be found.
#
# To work around this problem we symlink /tool/node_modules into the /src dir
# and then run remarklint
rm -f /src/node_modules
ln -s -f /tool/node_modules /src/node_modules

/src/node_modules/.bin/remark "$@"
