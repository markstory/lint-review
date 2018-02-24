FROM alpine:3.7

RUN mkdir /src \
  && mkdir /tool \
  && apk update \
  && apk add build-base curl lua5.3 lua5.3-dev unzip \
  # Get luarocks
  && curl -fsSL https://luarocks.org/releases/luarocks-2.4.3.tar.gz -o /tmp/luarocks.tar.gz \
  && tar -C /tmp -zxpf /tmp/luarocks.tar.gz \
  && cd /tmp/luarocks-2.4.3 \
  # Build luarocks
  && ./configure \
  && make bootstrap \
  && luarocks install luacheck \
  # Cleanup
  && rm /tmp/luarocks.tar.gz \
  && rm -rf /tmp/luarocks-2.4.3 \
  && apk del curl build-base \
  && rm -rf /var/cache/apk/*

WORKDIR /src
