FROM ruby:2.6-alpine

RUN mkdir /src \
  && mkdir /tool \
  && apk update \
  && apk add make libc-dev linux-headers gcc libffi-dev libxml2-dev libxml2 libxslt libxslt-dev \
  && rm -rf /var/cache/apk/*

COPY Gemfile /tool

# Install linters
RUN cd /tool \
  # Work around nokogiri failing to apply patches.
  && bundle config build.nokogiri --use-system-libraries \
  && bundle install

WORKDIR /src
