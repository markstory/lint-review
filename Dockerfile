FROM python:2.7
ENV REFRESHED_AT 2016-05-21

RUN apt-key adv --keyserver hkp://keyserver.ubuntu.com:80 --recv-keys 1655A0AB68576280 && \
    echo 'deb http://deb.nodesource.com/node_6.x jessie main' > /etc/apt/sources.list.d/nodesource-jessie.list

RUN apt-get update && apt-get install -y \
    php-pear \
    ruby \
    nodejs \
    ruby1.9.1 \
    ruby-dev \
    shellcheck \
    build-essential && \
    apt-get -y autoremove && \
    apt-get -y clean  && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /code
RUN pear install PHP_CodeSniffer
RUN gem install bundler

ADD package.json /code/
RUN npm install

ENV BUNDLE_SILENCE_ROOT_WARNING 1
ADD Gemfile Gemfile.lock /code/
RUN bundler install --system

ADD requirements.txt /code/
RUN pip install -r requirements.txt
ADD . /code
RUN pip install .
RUN cp /code/settings.sample.py /code/settings.py
