FROM python:2.7-alpine

RUN mkdir /src \
  && mkdir /tool \
  && apk update \
  && apk add gcc libffi-dev

COPY requirements.txt /tool

# Install linters
RUN cd /tool \
  && pip install -r requirements.txt

WORKDIR /src
