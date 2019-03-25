import os
import json


def env(key, default=None, cast=str):
    value = os.environ.get(key, default)
    if value is None:
        return None
    return cast(value)


# Webserver configuration
#########################

# gunicorn config
bind = env('LINTREVIEW_GUNICORN_BIND', '127.0.0.1:5000')
errorlog = env('LINTREVIEW_GUNICORN_LOG_ERROR',
               'lintreview.error.log')
accesslog = env('LINTREVIEW_GUNICORN_LOG_ACCESS',
                'lintreview.access.log')
debug = env('LINTREVIEW_GUNICORN_DEBUG', True, bool)
loglevel = env('LINTREVIEW_GUNICORN_LOGLEVEL', 'debug')

# Basic flask config
DEBUG = env('LINTREVIEW_FLASK_DEBUG', True, bool)
TESTING = env('LINTREVIEW_TESTING', True, bool)
if os.environ.get('LINTREVIEW_SERVER_NAME') is not None:
    SERVER_NAME = env('LINTREVIEW_SERVER_NAME')

# Config file for logging
LOGGING_CONFIG = './logging.ini'


# Celery worker configuration
#############################
from kombu import Exchange, Queue

# AMQP or other celery broker URL.
# amqp paths should be in the form of user:pass@host:port//virtualhost
BROKER_URL = 'amqp://'+''.join([
    env('LINTREVIEW_MQ_USER', 'guest'), ':',
    env('LINTREVIEW_MQ_PASS', 'guest'), '@',
    env('LINTREVIEW_MQ_HOST', 'broker'), ':',
    env('LINTREVIEW_MQ_PORT', '5672'), '/',
    env('LINTREVIEW_MQ_VIRTUAL_HOST', '/')
])

# Use json for serializing messages.
CELERY_TASK_SERIALIZER = 'json'
CELERY_ACCEPT_CONTENT = ['json']

# Show dates and times in UTC
CELERY_ENABLE_UTC = True


# General project configuration
###############################

# Path where project code should be
# checked out when reviews are done
# Repos will be checked out into $WORKSPACE/$user/$repo/$number
# directories to prevent collisions.
WORKSPACE = env('LINTREVIEW_WORKSPACE', '/tmp/workspace')

# This config file contains default settings for .lintrc
# LINTRC_DEFAULTS = './lintrc_defaults.ini'


# Github Configuration
######################

# Use GITHUB_URL when working with github:e
GITHUB_URL = env('GITHUB_URL', 'https://api.github.com/')

# You can also use an Oauth token for github, if you do
# uncomment this line. Using a token will take precedence
# over a username and password.
GITHUB_OAUTH_TOKEN = env('GITHUB_OAUTH_TOKEN', None)

# This is a dictionary used to initialize the Retry object used by
# the Github3.py GitHub client object. Specify valid keyword args
# to customize retry behavior.
# eg GITHUB_CLIENT_RETRY_OPTIONS='{"backoff_factor" : 0.3}'
#
# NOTE: the value of the GITHUB_CLIENT_RETRY_OPTIONS environment variable
# MUST be valid json.
#
# See documentation for urllib3.util.retry.Retry for available options.
#
# Default Retry settings are used if no config is provided.
GITHUB_CLIENT_RETRY_OPTIONS = env('GITHUB_CLIENT_RETRY_OPTIONS', None, json.loads)

# Set to a path containing a custom CA bundle.
# This is useful when you have github:enterprise on an internal
# network with self-signed certificates.
SSL_CA_BUNDLE = None

# After this many comments in a review, a single summary comment
# should be posted instead of individual line comments. This helps
# prevent really noisy reviews from slowing down github.
SUMMARY_THRESHOLD = env('LINTREVIEW_SUMMARY_THRESHOLD', 50, int)

# Used as the author information when making commits
GITHUB_AUTHOR_NAME = env('LINTREVIEW_GITHUB_AUTHOR_NAME', 'lintreview')
GITHUB_AUTHOR_EMAIL = env('LINTREVIEW_GITHUB_AUTHOR_EMAIL',
                          'lintreview@example.com')

# Status Configuration
######################
# Customize the build status integration name. Defaults to lintreview.
# APP_NAME = 'lintreview'

# Publish failing result as pull requests status
# If false, reviews with comments will get a 'success' build status.
PULLREQUEST_STATUS = env('LINTREVIEW_PULLREQUEST_STATUS', True, bool)

# Uncomment this option to enable adding an issue comment
# whenever a pull request passes all checks.
# eg: OK_COMMENT = ':+1: No lint errors found.'
OK_COMMENT = env('LINTREVIEW_OK_COMMENT', '')

# Enable to apply a label when updating build status.
# Pull requests that fail will have the label removed.
# Customize the label name when label statuses are enabled.
# eg: OK_LABEL = 'No lint errors'
OK_LABEL = env('LINTREVIEW_OK_LABEL', '')
