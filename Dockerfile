FROM python:2.7
ENV REFRESHED_AT 2016-05-21
RUN apt-get update && apt-get install -y \
    php-pear \
    ruby \
    npm \
    ruby1.9.1 \
    ruby-dev \
    shellcheck \
    build-essential && \
    apt-get -y autoremove && \
    apt-get -y clean  && \
    rm -rf /var/lib/apt/lists/*
WORKDIR /code
RUN pear install PHP_CodeSniffer
RUN ln -s /usr/bin/nodejs /usr/bin/node
RUN gem install bundler && bundle install --system

ADD composer.json composer.lock /code/
RUN composer install

ADD package.json /code/
RUN npm install

ADD Gemfile Gemfile.lock /code/
RUN bundler install --system

ADD requirements.txt /code/
RUN pip install -r requirements.txt
ADD . /code
RUN pip install .
RUN cp /code/settings.sample.py /code/settings.py
