FROM node:8-alpine

RUN mkdir /src \
  && mkdir /tool

COPY package.json /tool

# Install node tools
RUN cd /tool \
  && npm install \
  # Make npm executables quack like binaries.
  && ln -s /tool/node_modules/.bin/{eslint,csslint,jscs,sass-lint,tslint,standardjs,xo} /usr/bin

WORKDIR /src
