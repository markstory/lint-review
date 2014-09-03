# Webserver configuration #
###########################

# gunicorn config
bind = '127.0.0.1:5000'
errorlog = 'lintreview.error.log'
accesslog = 'lintreview.access.log'
debug = True
loglevel = 'debug'

# Basic flask config
DEBUG = True
TESTING = True
SERVER_NAME = '127.0.0.1:5000'

# Config file for logging
LOGGING_CONFIG = './logging.ini'


# Celery worker configuration #
###############################
from kombu import Exchange, Queue

# AMQP or other celery broker URL.
# amqp paths should be in the form of user:pass@host:port//virtualhost
BROKER_URL = 'amqp://'

# Use json for serializing messages.
CELERY_TASK_SERIALIZER = 'json'

# Show dates and times in UTC
CELERY_ENABLE_UTC = True

# Set the queues that celery will use.
CELERY_QUEUES = (
    Queue('lint', Exchange('lintreview'), routing_key='linty'),
)


# General project configuration #
#################################
import os

# Path where project code should be
# checked out when reviews are done
# Repos will be checked out into $WORKSPACE/$user/$repo/$number
# directories to prevent collisions.
WORKSPACE = './workspace'

# Use GITHUB_URL when working with github:e
# When working with github:e don't forget to add the /api/v3/ path
GITHUB_URL = 'https://api.github.com/'

# Github username + password
# This is the user that lintreview will use
# to fetch repositories and leave review comments.
# Set the GITHUB_PASSWORD environment variable first.
# example: $ export GITHUB_PASSWORD=mygithubpassword
GITHUB_USER = 'octocat'
GITHUB_PASSWORD = os.environ.get('GITHUB_PASSWORD', '')

# You can also use an Oauth token for github, if you do
# uncomment this line. Using a token will take precedence
# over a username and password.
# GITHUB_OAUTH_TOKEN = None

# Set to a path containing a custom CA bundle.
# This is useful when you have github:enterprise on an internal
# network with self-signed certificates.
SSL_CA_BUNDLE = None

# After this many comments in a review, a single summary comment
# should be posted instead of individual line comments. This helps
# prevent really noisy reviews from slowing down github.
SUMMARY_THRESHOLD = 50

OK_COMMENT = ':+1: No lint errors found.'
