#!/bin/bash
git config --global user.name dockerbot
git config --global user.email dockerbot@example.com

pip install -r requirements-dev.txt

pytest \
    -p no:cacheprovider \
    --cov=lintreview \
    --cov-report=xml:/data/results/coverage.xml \
    --junitxml=/data/results/nosetests.xml
