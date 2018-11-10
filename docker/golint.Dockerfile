FROM golang:1.11-alpine

ENV GOPATH=/tool/golang

RUN mkdir /tool \
  && mkdir /src \
  && apk update \
  && apk add build-base git curl \
  # Install golint
  && go get -u golang.org/x/lint/golint \
  && ln -s /tool/golang/bin/golint /usr/bin/golint \
  # Install golangci-lint
 && curl -sfL https://raw.githubusercontent.com/golangci/golangci-lint/master/install.sh | sh -s -- -b $GOPATH/bin v1.12 \
  && ln -s /tool/golang/bin/golangci-lint /usr/bin/golangci-lint \
  # Cleanup
  && apk del build-base git curl \
  && rm -rf /var/cache/apk/*

WORKDIR /src
