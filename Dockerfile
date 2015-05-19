FROM python:2.7
WORKDIR /code
ADD . /code
ENV LINTREVIEW_SETTINGS /code/settings.sample.py
RUN apt-get upgrade -y && apt-get update && \
    apt-get install -y php-pear ruby npm && \
    apt-get install -y ruby1.9.1 ruby-dev build-essential && \
    apt-get -y autoremove && apt-get -y clean
RUN pip install -r requirements.txt && pip install .
RUN pear install PHP_CodeSniffer
RUN gem install bundler && bundle install --system
RUN npm install -y csslint jshint
RUN ln -s /usr/bin/nodejs /usr/bin/node
RUN nosetests -v
