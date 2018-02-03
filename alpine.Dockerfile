FROM node:8.9.4-alpine
RUN apk add --no-cache \
        gcc=6.3.0-r4 \
        git=2.13.5-r0 \
        libffi-dev=3.2.1-r3 \
        libxml2=2.9.5-r0 \
        musl-dev=1.1.16-r14 \
        openssl-dev=1.0.2n-r0 \
        openssl=1.0.2n-r0 \
        python2=2.7.13-r1 \
        python-dev=2.7.13-r1 \
        py-pip=9.0.1-r1 \
        zlib-dev=1.2.11-r0

WORKDIR /code
ADD requirements.txt ./
RUN pip install -r requirements.txt
ADD . ./
RUN pip install . \
 && cp settings.sample.py settings.py
