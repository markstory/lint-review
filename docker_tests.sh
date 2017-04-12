#!/bin/bash

pip install -r requirements-dev.txt
pip install codecov coverage

nosetests --with-coverage --cover-package lintreview
