# Use debian instead of alpine as ninja (a dep of pytype)
# doesn't build with musl because of timestamp struct problems
FROM python:3.7-slim-stretch

RUN apt-get update \
  && apt-get install -y --no-install-recommends \
    gcc \
    build-essential \
  && rm -rf /var/lib/apt/lists/*

RUN mkdir /src \
  && mkdir /tool

COPY requirements-py3.txt /tool
COPY merge-pyi-wrapper.sh /usr/bin/merge-pyi-wrapper
COPY flake8-install.sh /usr/bin/flake8-install

# Install linters & wrapper script
RUN cd /tool \
  && pip install -r requirements-py3.txt \
  && chmod +x /usr/bin/merge-pyi-wrapper \
  && chmod +x /usr/bin/flake8-install

WORKDIR /src
