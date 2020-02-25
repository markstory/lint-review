FROM openjdk:15-alpine

# Install ktlint
ARG ktlint_version=0.36.0
RUN apk add --no-cache curl gnupg
RUN curl -sSLO https://github.com/pinterest/ktlint/releases/download/${ktlint_version}/ktlint && \
    chmod a+x ktlint && \
    mv ktlint /usr/local/bin/

RUN mkdir /src \
  && mkdir /tool \
  && apk update \
  && rm -rf /var/cache/apk/*

WORKDIR /src
