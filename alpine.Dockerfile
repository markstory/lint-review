FROM alpine:3.7
RUN apk add --no-cache \
        curl=7.57.0-r0 \
        gcc=6.4.0-r5 \
        git=2.15.0-r1 \
        libffi-dev=3.2.1-r4 \
        libxml2=2.9.7-r0 \
        musl-dev=1.1.18-r2 \
        openssl-dev=1.0.2n-r0 \
        openssl=1.0.2n-r0 \
        python2=2.7.14-r2 \
        python2-dev=2.7.14-r2 \
        py2-pip=9.0.1-r1 \
        zlib-dev=1.2.11-r1

WORKDIR /code
ADD requirements.txt ./
RUN pip install -r requirements.txt
ADD . ./
RUN pip install . \
 && cp settings.sample.py settings.py
