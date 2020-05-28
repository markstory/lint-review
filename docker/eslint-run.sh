#!/bin/bash

# Eslint 6 assumes that all config/plugin
# modules are installed relative to the cwd/where
# eslint is run. However, because we install packages in
# /tool we need to trick eslint with a symlink
rm -f /src/node_modules
ln -s -f /tool/node_modules /src/node_modules

exec "$@"
