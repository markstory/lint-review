FROM ubuntu:16.04
ENV REFRESHED_AT 2018-02-24
ENV LANG=en_US.UTF-8

RUN apt-get update && \
    apt-get install -y \
    python2.7 python-pip \
    git \
    libxml2 \
    libffi-dev \
    zlib1g-dev \
    docker.io \
    build-essential && \
    apt-get -y autoremove && \
    apt-get -y clean  && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /code

ADD . /code
ADD requirements.txt /code/
RUN cd /code && pip install -r requirements.txt
RUN cd /code && pip install .
RUN cp /code/settings.sample.py /code/settings.py
