FROM python:3.8-alpine

RUN mkdir /src \
  && mkdir /tool

RUN apk update \
  && apk add openssl-dev make libc-dev linux-headers gcc libffi-dev \
  && rm -rf /var/cache/apk/*

COPY requirements-py3.txt /tool
COPY flake8-install.sh /usr/bin/flake8-install

# Install linters & wrapper script
RUN cd /tool \
  && pip install -r requirements-py3.txt \
  && chmod +x /usr/bin/flake8-install

WORKDIR /src
