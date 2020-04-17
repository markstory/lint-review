#!/bin/sh

# PHPCS configurations often rely on using
# the `installed_paths` configuration option to configure
# paths to inherited configuration. Add symlinks so that
# inheriting from an installed standard works.
rm -f /src/vendor
ln -s -f /tool/vendor /src/vendor

exec "$@"
