FROM alpine:3.7

ENV SHELLCHECK_DOWNLOAD_URL https://shellcheck.storage.googleapis.com/shellcheck-v0.4.7.linux.x86_64.tar.xz
ENV SHELLCHECK_DOWNLOAD_SHA512 64bf19a1292f0357c007b615150b6e58dba138bc7bf168c5a5e27016f8b4f802afd9950be8be46bf9e4833f98ae81c6e7b1761a3a76ddbba2a04929265433134

RUN mkdir /tool \
  && mkdir /src

RUN apk update \
  && apk add curl xz \
  && curl -fsSL "$SHELLCHECK_DOWNLOAD_URL" -o /tool/shellcheck.tar.xz \
  && echo "$SHELLCHECK_DOWNLOAD_SHA512  /tool/shellcheck.tar.xz" | sha512sum -c - \
  && tar -C /tool -xJf /tool/shellcheck.tar.xz \
  && mv /tool/shellcheck-v0.4.7/shellcheck /usr/bin \
  && rm /tool/shellcheck.tar.xz \
  && rm -rf /tool/shellcheck-v0.4.7 \
  # Cleanup
  && apk del curl xz \
  && rm -rf /var/cache/apk/*

WORKDIR /src
