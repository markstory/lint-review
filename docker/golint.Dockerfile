FROM golang:1.11

ENV GOPATH=/tool/golang
ENV GOBINPATH=$GOPATH/bin
ENV PATH=$PATH:/usr/local/go/bin:$GOBINPATH

RUN mkdir -p /tool/golang/bin /src

# Install dep
ENV DEP_RELEASE_TAG=v0.5.0
RUN curl https://raw.githubusercontent.com/golang/dep/master/install.sh | sh

# Install godep
ENV GODEP_VERSION=v80
RUN curl -sL -o $GOBINPATH/godep https://github.com/tools/godep/releases/download/${GODEP_VERSION}/godep_linux_amd64 \
  && chmod a+x $GOBINPATH/godep

# Install govendor
ENV GOVENDOR_VERSION=v1.0.8
RUN curl -sL -o $GOBINPATH/govendor https://github.com/kardianos/govendor/releases/download/${GOVENDOR_VERSION}/govendor_linux_amd64 \
  && chmod a+x $GOBINPATH/govendor

# Install golint
RUN go get -u golang.org/x/lint/golint

# Install golangci-lint
RUN curl -sL https://raw.githubusercontent.com/golangci/golangci-lint/master/install.sh | sh -s -- -b $GOPATH/bin v1.12.2

# Cleanup
RUN apt-get clean

WORKDIR /src
