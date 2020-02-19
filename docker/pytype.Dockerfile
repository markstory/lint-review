# Use debian instead of alpine as ninja (a dep of pytype)
# doesn't build with musl because of timestamp struct problems
FROM python:3.7-slim-buster

RUN apt-get update \
  && apt-get install -y --no-install-recommends \
    gcc \
    build-essential \
  && rm -rf /var/lib/apt/lists/*

RUN mkdir /src \
  && mkdir /tool

COPY pytype-requirements.txt /tool
COPY merge-pyi-wrapper.sh /usr/bin/merge-pyi-wrapper

# Install linters & wrapper script
RUN cd /tool \
  && pip install -r pytype-requirements.txt \
  && chmod +x /usr/bin/merge-pyi-wrapper

WORKDIR /src
