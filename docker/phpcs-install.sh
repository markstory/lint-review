#!/bin/sh
cd /tool || exit 1

php /tool/composer.phar require "$1"
