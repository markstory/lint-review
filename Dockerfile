FROM ubuntu:16.04
ENV REFRESHED_AT 2018-02-24

RUN apt-get update && \
    apt-get install -y curl && \
    curl -sL https://deb.nodesource.com/setup_6.x | bash -

RUN apt-get install -y \
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

ADD requirements.txt /code/
RUN pip install -r requirements.txt
ADD . /code
RUN pip install .
RUN cp /code/settings.sample.py /code/settings.py
