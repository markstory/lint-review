#!/usr/bin/env python

# Run the flask application that accepts
# webhooks from github.
from lintreview.web import app
from optparse import OptionParser


def main():
    parser = OptionParser()
    parser.add_option('-d', '--debug',
                      action='store_true', dest='debug', default=False,
                      help='Enable the flask debugger.')
    parser.add_option('-b', '--bind-address',
                      action='store', dest='host', default='0.0.0.0',
                      type='string',
                      help='The ip address to bind to.')
    parser.add_option('-p', '--port',
                      action='store', dest='port', default='5000',
                      type='int',
                      help='The port to bind onto.')
    (options, args) = parser.parse_args()

    app.debug = options.debug
    app.run(host=options.host, port=options.port)


if __name__ == '__main__':
    main()
