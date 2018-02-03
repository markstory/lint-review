FROM ubuntu:16.04
ENV REFRESHED_AT 2016-05-21

RUN apt-get update && \
    apt-get install -y curl && \
    curl -sL https://deb.nodesource.com/setup_6.x | bash -

RUN apt-get install -y \
    python2.7 python-pip \
    php \
    php-pear \
    git \
    ruby \
    nodejs \
    ruby \
    ruby-dev \
    shellcheck \
    luarocks \
    libxml2 \
    libffi-dev \
    zlib1g-dev \
    build-essential && \
    apt-get -y autoremove && \
    apt-get -y clean  && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /code
RUN pear install PHP_CodeSniffer
RUN luarocks install luacheck
RUN gem install bundler

ADD package.json /code/
RUN npm install

ENV BUNDLE_SILENCE_ROOT_WARNING 1
ADD Gemfile Gemfile.lock /code/
RUN bundler install --system

ADD requirements.txt requirements-linters.txt /code/
RUN pip install -r requirements.txt -r requirements-linters.txt
ADD . /code
RUN pip install .
RUN cp /code/settings.sample.py /code/settings.py
