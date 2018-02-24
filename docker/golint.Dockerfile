FROM alpine:3.7

# Install go 1.8 from tarball
ENV GOLANG_VERSION 1.8.5
ENV GOLANG_DOWNLOAD_URL https://golang.org/dl/go$GOLANG_VERSION.linux-amd64.tar.gz
ENV GOLANG_DOWNLOAD_SHA256 4f8aeea2033a2d731f2f75c4d0a4995b357b22af56ed69b3015f4291fca4d42d
ENV GOPATH=/tool/golang

RUN mkdir /tool \
  && mkdir /src \
  && apk update \
  && apk add build-base go git \
  # Install golint
  && go get github.com/golang/lint/golint \
  && ln -s /tool/golang/bin/golint /usr/bin/golint \
  # Cleanup
  && apk del build-base git curl \
  && rm -rf /var/cache/apk/*

WORKDIR /src
