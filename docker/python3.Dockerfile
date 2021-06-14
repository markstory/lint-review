FROM python:3.8-slim-buster

RUN mkdir /src \
  && mkdir /tool


RUN apt-get update \
  && apt-get install -y --no-install-recommends \
    gcc build-essential \
  && rm -rf /var/lib/apt/lists/*

COPY requirements-py3.txt /tool
COPY flake8-install.sh /usr/bin/flake8-install

# Install linters & wrapper script
RUN cd /tool \
  && pip install -r requirements-py3.txt \
  && chmod +x /usr/bin/flake8-install

WORKDIR /src
