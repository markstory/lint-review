FROM python:2.7-alpine

RUN mkdir /src \
  && mkdir /tool \
  && apk update \
  && apk add openssl-dev make libc-dev linux-headers gcc libffi-dev \
  && rm -rf /var/cache/apk/*

COPY requirements.txt /tool

# Install linters
RUN cd /tool \
  && pip install -r requirements.txt

WORKDIR /src
