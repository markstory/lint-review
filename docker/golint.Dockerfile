FROM golang:1.11

ENV GOPATH=/golang
ENV GOBINPATH=$GOPATH/bin
ENV GOBIN=$GOBINPATH
ENV PATH=$PATH:/usr/local/go/bin:$GOBINPATH

RUN mkdir -p /golang/bin /golang/src
RUN ln -s /src /golang/src/app

# Install golint
RUN go get -u golang.org/x/lint/golint

# Cleanup
RUN apt-get clean

WORKDIR /src
