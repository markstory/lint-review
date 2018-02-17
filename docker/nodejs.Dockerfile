FROM node:8-alpine

RUN mkdir /src \
  && mkdir /tool

COPY package.json /tool

# Install node tools
RUN cd /tool \
  && npm install \
  # Make npm executables quack like binaries.
  && ln -s /tool/node_modules/.bin/eslint /usr/bin/eslint \
  && ln -s /tool/node_modules/.bin/csslint /usr/bin/csslint \
  && ln -s /tool/node_modules/.bin/jscs /usr/bin/jscs \
  && ln -s /tool/node_modules/.bin/sass-lint /usr/bin/sass-lint \
  && ln -s /tool/node_modules/.bin/standard /usr/bin/standard \
  && ln -s /tool/node_modules/.bin/tslint /usr/bin/tslint \
  && ln -s /tool/node_modules/.bin/xo /usr/bin/xo

WORKDIR /src
