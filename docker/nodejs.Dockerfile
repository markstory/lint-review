FROM node:8-alpine

RUN mkdir /src \
  && mkdir /tool \
  && apk --update add bash \
  # Upgrade npm to get around pruning issues.
  && npm install npm@latest -g \
  && rm -rf /var/cache/apk/*

COPY package.json /tool
COPY eslint-install.sh /usr/bin/eslint-install

# Install node tools
RUN cd /tool \
  && npm install \
  # Make npm executables quack like binaries.
  && ln -s /tool/node_modules/.bin/eslint /usr/bin/eslint \
  && ln -s /tool/node_modules/.bin/csslint /usr/bin/csslint \
  && ln -s /tool/node_modules/.bin/jscs /usr/bin/jscs \
  && ln -s /tool/node_modules/.bin/jshint /usr/bin/jshint \
  && ln -s /tool/node_modules/.bin/sass-lint /usr/bin/sass-lint \
  && ln -s /tool/node_modules/.bin/standard /usr/bin/standard \
  && ln -s /tool/node_modules/.bin/tslint /usr/bin/tslint \
  && ln -s /tool/node_modules/.bin/xo /usr/bin/xo \
  # Move package.json so that it is an ancestor of /src allowing
  # eslint and xo to use it for config
  && cp /tool/package.json / \
  && chmod +x /usr/bin/eslint-install

WORKDIR /src
