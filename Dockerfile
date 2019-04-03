FROM python:2.7.16-slim-stretch
ENV REFRESHED_AT 2019-03-31
ENV LANG=en_US.UTF-8
ENV LC_ALL=en_US.UTF-8

RUN apt-get update && apt-get install -y git curl

WORKDIR /code
# This allows us to cache the pip install stage
ADD requirements.txt /
RUN pip install -r /requirements.txt

ADD . /code
RUN pip install -e .
RUN cp /code/settings.sample.py /code/settings.py
