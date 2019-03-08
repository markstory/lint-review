FROM openjdk:8-alpine

# Install ktlint
ARG ktlint_version=0.30.0
RUN apk add --no-cache curl gnupg
RUN curl -sSLO https://github.com/shyiko/ktlint/releases/download/${ktlint_version}/ktlint && \
    curl -sSLO https://github.com/shyiko/ktlint/releases/download/${ktlint_version}/ktlint.asc && \
    curl -sS https://keybase.io/shyiko/pgp_keys.asc | gpg --import && gpg --verify ktlint.asc && \
    chmod a+x ktlint && \
    rm ktlint.asc && \
    mv ktlint /usr/local/bin/

RUN mkdir /src \
  && mkdir /tool \
  && apk update \
  && rm -rf /var/cache/apk/*

WORKDIR /src