FROM python:3.6-alpine

RUN mkdir /src \
  && mkdir /tool \
  && apk add musl-dev gcc  \
  && rm -rf /var/cache/apk/*

COPY requirements-py3.txt /tool

# Install linters
RUN cd /tool \
  && pip install -r requirements-py3.txt

WORKDIR /src
