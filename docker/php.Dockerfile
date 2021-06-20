FROM php:8.0-alpine

RUN mkdir /src \
  && mkdir /tool

RUN apk update \
  && apk add libzip-dev \
  && docker-php-ext-install zip \
  && rm -rf /var/cache/apk/*

COPY composer.json /tool
COPY phpcs-install.sh /usr/bin/phpcs-install
COPY phpcs-run.sh /usr/bin/phpcs-run

# Get composer, install PHP tools and remove composer.
RUN cd /tool \
  && php -r "copy('https://getcomposer.org/installer', 'composer-setup.php');" \
  && php composer-setup.php --install-dir /tool \
  && php /tool/composer.phar install \
  # make phpcs quack like a system binary
  && ln -s /tool/vendor/bin/phpcs /usr/bin/phpcs \
  && ln -s /tool/vendor/bin/phpcbf /usr/bin/phpcbf \
  && ln -s /tool/vendor/bin/phpmd /usr/bin/phpmd \
  # executable installer & wrapper scripts
  && chmod +x /usr/bin/phpcs-install \
  && chmod +x /usr/bin/phpcs-run \
  # Add coding standards to phpcs
  && vendor/bin/phpcs --config-set installed_paths /tool/vendor/cakephp/cakephp-codesniffer

WORKDIR /src
