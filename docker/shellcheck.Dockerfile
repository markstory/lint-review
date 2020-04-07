FROM koalaman/shellcheck-alpine:v0.7.1

RUN mkdir /tool \
  && mkdir /src

WORKDIR /src
