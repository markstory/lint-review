#!/bin/bash
git config --global user.name dockerbot
git config --global user.email dockerbot@example.com

pip install -r requirements-dev.txt
pip install codecov coverage

nosetests --with-coverage --cover-package lintreview
