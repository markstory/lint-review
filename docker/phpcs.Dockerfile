FROM php:7.2

RUN mkdir /src \
  && mkdir /composer

RUN apt-get update \
  && apt-get install -y zip libzip-dev \
  && docker-php-ext-install zip \
  && apt-get -y autoremove \
  && apt-get -y clean \
  && rm -rf /var/lib/apt/lists/*

COPY composer.json /composer

# Get composer, install PHP tools and remove composer.
RUN cd /composer \
  && php -r "copy('https://getcomposer.org/installer', 'composer-setup.php');" \
  && php composer-setup.php --install-dir /composer \
  && php /composer/composer.phar install \
  # make phpcs quack like a system binary
  && ln -s /composer/vendor/bin/phpcs /usr/bin/phpcs \
  && ln -s /composer/vendor/bin/phpcbf /usr/bin/phpcbf \
  # Add coding standards to phpcs
  && vendor/bin/phpcs --config-set installed_paths /composer/vendor/cakephp/cakephp-codesniffer \
  # cleanup
  && rm /composer/composer.phar /composer/composer-setup.php /composer/composer.json /composer/composer.lock

WORKDIR /src
