FROM python:2.7
WORKDIR /code
ADD . /code
ENV LINTREVIEW_SETTINGS /code/settings.sample.py
RUN apt-get update && apt-get install -y php-pear ruby npm && \
    pip install -r requirements.txt && pip install . && \
    pear install PHP_CodeSniffer && \
    gem install bundler && bundle install --system && \
    npm install -y csslint jshint && \
    ln -s /usr/bin/nodejs /usr/bin/node && \
    apt-get -y autoremove && apt-get -y clean && \
    nosetests -v
