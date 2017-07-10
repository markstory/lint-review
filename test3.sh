#!/bin/bash

docker build -f Dockerfile-py3  . --tag=lr-py3
docker run -ti lr-py3 /code/docker_tests.sh
