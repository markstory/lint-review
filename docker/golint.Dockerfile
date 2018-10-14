FROM alpine:3.7

ENV GOPATH=/tool/golang

RUN mkdir /tool \
  && mkdir /src \
  && apk update \
  && apk add build-base go git \
  # Install golint
  && go get -u golang.org/x/lint/golint \
  && ln -s /tool/golang/bin/golint /usr/bin/golint \
  # Cleanup
  && apk del build-base git curl \
  && rm -rf /var/cache/apk/*

WORKDIR /src
