FROM python:3.6-alpine

RUN mkdir /src \
  && mkdir /tool

COPY requirements-py3.txt /tool

# Install linters
RUN cd /tool \
  && pip install -r requirements-py3.txt

WORKDIR /src
