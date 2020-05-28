# Eslint requires its own docker file
# because eslint 5.x has a number of incompatibilities
# with other eslint based tools like xo and standardjs
FROM node:12-alpine

RUN mkdir /src \
  && mkdir /tool \
  && apk --update add bash \
  # To handle 'not get uid/gid'
  && npm config set unsafe-perm true \
  # Upgrade yarn to get latest release
  && npm install yarn@latest --force -g \
  && rm -rf /var/cache/apk/*

COPY eslint-package.json /tool/package.json
COPY eslint-install.sh /usr/bin/eslint-install
COPY eslint-run.sh /usr/bin/eslint-run

# Install node tools
RUN cd /tool && yarn install

# Make npm executables quack like binaries.
RUN ln -s /tool/node_modules/.bin/eslint /usr/bin/eslint \
  && ln -s /tool/node_modules/.bin/install-peerdeps /usr/bin/install-peerdeps \
  # Copy package.json so that it is an ancestor of /src allowing
  # eslint and xo to use it for config
  && cp /tool/package.json / \
  && chmod +x /usr/bin/eslint-install \
  && chmod +x /usr/bin/eslint-run

WORKDIR /src
