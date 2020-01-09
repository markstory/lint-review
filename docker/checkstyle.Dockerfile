FROM alpine:3.7

RUN mkdir /tool && mkdir /src
COPY checkstyle-8.28-all.jar /tool/checkstyle.jar

RUN apk update \
  && apk add openjdk8-jre \
  # Make wrapper script for checkstyle
  && echo '#!/bin/sh' >> /usr/bin/checkstyle \
  && echo 'java -jar /tool/checkstyle.jar $@' >> /usr/bin/checkstyle \
  && chmod +x /usr/bin/checkstyle \
  # Cleanup
  && rm -rf /var/cache/apk/*

WORKDIR /src
