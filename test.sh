#!/bin/bash

docker build -f Dockerfile . --tag=lr-py2
docker run -ti lr-py2 /code/docker_tests.sh
