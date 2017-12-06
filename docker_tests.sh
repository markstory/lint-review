#!/bin/bash
git config --global user.name 'lintreview'
git config --global user.email 'lintbot@localhost'

pip install -r requirements-dev.txt
pip install codecov coverage

nosetests --with-coverage --cover-package lintreview
