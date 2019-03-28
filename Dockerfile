FROM ubuntu:16.04
ENV REFRESHED_AT 2018-02-24
ENV LANG=en_US.UTF-8
ENV LC_ALL=en_US.UTF-8

RUN apt-get update && \
    apt-get install -y \
    python2.7 python-pip \
    curl \
    git \
    libxml2 \
    libffi-dev \
    zlib1g-dev \
    docker.io \
    language-pack-en \
    build-essential && \
    dpkg-reconfigure locales && \
    apt-get -y autoremove && \
    apt-get -y clean  && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /code

# This allows us to cache the pip install stage
ADD requirements.txt /
RUN pip install -r /requirements.txt

ADD . /code
RUN pip install -e .
RUN cp /code/settings.sample.py /code/settings.py
