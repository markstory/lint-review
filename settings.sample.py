import os

# Webserver configuration #
###########################

# gunicorn config
bind = os.environ.get('LINTREVIEW_GUNICORN_BIND', '127.0.0.1:5000')
errorlog = os.environ.get('LINTREVIEW_GUNICORN_LOG_ERROR',
                          'lintreview.error.log')
accesslog = os.environ.get('LINTREVIEW_GUNICORN_LOG_ACCESS',
                           'lintreview.access.log')
debug = bool(os.environ.get('LINTREVIEW_GUNICORN_DEBUG', True))
loglevel = os.environ.get('LINTREVIEW_GUNICORN_LOGLEVEL', 'debug')

# Basic flask config
DEBUG = os.environ.get('LINTREVIEW_FLASK_DEBUG', True)
TESTING = os.environ.get('LINTREVIEW_TESTING', True)
SERVER_NAME = os.environ.get('LINTREVIEW_SERVER_NAME', '127.0.0.1:5000')

# Config file for logging
LOGGING_CONFIG = './logging.ini'


# Celery worker configuration #
###############################
from kombu import Exchange, Queue

# AMQP or other celery broker URL.
# amqp paths should be in the form of user:pass@host:port//virtualhost
BROKER_URL = 'amqp://'+''.join([
    os.environ.get('LINTREVIEW_MQ_USER', 'guest'), ':',
    os.environ.get('LINTREVIEW_MQ_PASS', 'guest'), '@',
    os.environ.get('LINTREVIEW_MQ_HOST',
    os.environ.get('BROKER_PORT_5672_TCP_ADDR', '127.0.0.1')), ':',
    os.environ.get('LINTREVIEW_MQ_PORT',
    os.environ.get('BROKER_PORT_5672_TCP_PORT', '5672')), '/',
    os.environ.get('LINTREVIEW_MQ_VIRTUAL_HOST', '/')
])

# Use json for serializing messages.
CELERY_TASK_SERIALIZER = 'json'

# Show dates and times in UTC
CELERY_ENABLE_UTC = True


# General project configuration #
#################################

# Path where project code should be
# checked out when reviews are done
# Repos will be checked out into $WORKSPACE/$user/$repo/$number
# directories to prevent collisions.
WORKSPACE = os.environ.get('LINTREVIEW_WORKSPACE', '/tmp/workspace')

# Use GITHUB_URL when working with github:e
# When working with github:e don't forget to add the /api/v3/ path
GITHUB_URL = os.environ.get('GITHUB_URL', 'https://api.github.com/')

# Github username + password
# This is the user that lintreview will use
# to fetch repositories and leave review comments.
# Set the GITHUB_PASSWORD environment variable first.
# example: $ export GITHUB_PASSWORD=mygithubpassword
GITHUB_USER = os.environ.get('GITHUB_USERNAME', 'octocat')
GITHUB_PASSWORD = os.environ.get('GITHUB_PASSWORD', '')

# You can also use an Oauth token for github, if you do
# uncomment this line. Using a token will take precedence
# over a username and password.
GITHUB_OAUTH_TOKEN = os.environ.get('GITHUB_OAUTH_TOKEN', None)

# Set to a path containing a custom CA bundle.
# This is useful when you have github:enterprise on an internal
# network with self-signed certificates.
SSL_CA_BUNDLE = None

# After this many comments in a review, a single summary comment
# should be posted instead of individual line comments. This helps
# prevent really noisy reviews from slowing down github.
SUMMARY_THRESHOLD = int(os.environ.get('LINTREVIEW_SUMMARY_THRESHOLD', 50))

# This config file contains default settings for .lintrc
# LINTRC_DEFAULTS = './lintrc_defaults.ini'

OK_COMMENT = os.environ.get('LINTREVIEW_OK_COMMENT',
                            ':+1: No lint errors found.')

# Set to True to use a label instead of a comment for OK status.
# Cuts down on github notification noise.
ADD_OK_LABEL = bool(os.environ.get('LINTREVIEW_ADD_OK_LABEL', False))
OK_LABEL = os.environ.get('LINTREVIEW_OK_LABEL', 'No lint errors')
