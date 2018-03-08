FROM ruby:2.4-alpine

RUN mkdir /src \
  && mkdir /tool \
  && apk update \
  && apk add make libc-dev linux-headers gcc libffi-dev \
  && rm -rf /var/cache/apk/*

COPY Gemfile /tool

# Install linters
RUN cd /tool \
  && bundle install

WORKDIR /src
