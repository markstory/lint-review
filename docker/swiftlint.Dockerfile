FROM norionomura/swiftlint:0.32.0

RUN mkdir /tool \
  && mkdir /src

WORKDIR /src
