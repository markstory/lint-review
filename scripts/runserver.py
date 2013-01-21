#!/usr/bin/env python

# Run the flask application that accepts
# webhooks from github.
from lintreview.web import app
import argparse


def main():
    desc = """Start the lintreview webserver.
    It handles webhooks from github.
    """

    parser = argparse.ArgumentParser(description=desc)
    parser.add_argument('-d, --debug',
            action="store_true",
            dest='debug',
            default=False,
            help='Enable the flask debugger.')
    parser.add_argument('-b, --bind-address',
            action='store',
            dest='host',
            default='0.0.0.0',
            type=str,
            help='The ip address to bind to.')
    parser.add_argument('-p, --port',
            action='store',
            dest='port',
            default='5000',
            type=int,
            help='The port to bind onto.')
    args = parser.parse_args()

    app.debug = args.debug
    app.run(host=args.host, port=args.port)


if __name__ == '__main__':
    main()
