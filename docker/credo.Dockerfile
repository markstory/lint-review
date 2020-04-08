FROM elixir:1.10-alpine

RUN apk add git

RUN mkdir /src \
  && mkdir /tool

RUN cd /tool \
  && git clone https://github.com/rrrene/bunt.git \
  && cd bunt \
  && mix local.hex --force \
  && mix archive.build \
  && mix archive.install --force \
  && cd - \
  && git clone https://github.com/rrrene/credo.git \
  && cd credo \
  && mix deps.get \
  && mix archive.build \
  && mix archive.install --force

WORKDIR /src
