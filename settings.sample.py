# Webserver configuration #
###########################

# gunicorn config
bind = '127.0.0.1:5000'
error_logfile = 'lintreview.error.log'
access_logfile = 'lintreview.access.log'
debug = True
log_level = 'debug'

# Basic flask config
DEBUG = True
TESTING = True
SERVER_NAME = '127.0.0.1:5000'

# Config file for logging
LOGGING_CONFIG = './logging.ini'


# Celery worker configuration #
###############################

BROKER_URL = 'amqp://'
CELERY_TASK_SERIALIZER = 'json'
CELERY_ENABLE_UTC = True


# General project configuration #
#################################

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
GITHUB_USER = 'octocat'
GITHUB_PASSWORD = ''
