FROM alpine:3.7

ENV CHECKSTYLE_URL https://downloads.sourceforge.net/project/checkstyle/checkstyle/7.7/checkstyle-7.7-all.jar

RUN mkdir /tool && mkdir /src

RUN apk update \
  && apk add curl openjdk8-jre \
  # Get checkstyle and make wrapper script
  && curl -fsSL "$CHECKSTYLE_URL" -o /tool/checkstyle.jar \
  && echo '#!/bin/sh' >> /usr/bin/checkstyle \
  && echo 'java -jar /tool/checkstyle.jar $@' >> /usr/bin/checkstyle \
  && chmod +x /usr/bin/checkstyle \
  # Cleanup
  && apk del curl \
  && rm -rf /var/cache/apk/*

WORKDIR /src
