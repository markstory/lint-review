# Container for all non-eslint tools.
# as eslint 5.0 doesn't play nice with standard and xo
FROM node:8-alpine

RUN mkdir /src \
  && mkdir /tool \
  && apk --update add bash \
  # To handle 'not get uid/gid'
  && npm config set unsafe-perm true \
  # Upgrade yarn to get latest release
  && npm install yarn@latest --force -g \
  && rm -rf /var/cache/apk/*

COPY package.json /tool
COPY run-remark.sh /usr/bin/run-remark

# Install node tools
RUN cd /tool && yarn install

# Make npm executables quack like binaries.
RUN ln -s /tool/node_modules/.bin/csslint /usr/bin/csslint \
  && ln -s /tool/node_modules/.bin/jshint /usr/bin/jshint \
  && ln -s /tool/node_modules/.bin/sass-lint /usr/bin/sass-lint \
  && ln -s /tool/node_modules/.bin/standard /usr/bin/standard \
  && ln -s /tool/node_modules/.bin/stylelint /usr/bin/stylelint \
  && ln -s /tool/node_modules/.bin/tslint /usr/bin/tslint \
  # Copy package.json so that it is an ancestor of /src allowing
  # stylelint can use it for config
  && cp /tool/package.json /

WORKDIR /src
