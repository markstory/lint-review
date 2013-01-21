# Basic flask config
DEBUG = True
TESTING = True

SERVER_NAME = None

# Use GITHUB_HOST when working with github:e
GITHUB_HOST = 'https://github.com'

# Github username + password
# This is the user that lintreview will use
# to fetch repositories and leave review comments.
GITHUB_USER = 'octocat'
GITHUB_PASS = ''

# Path where project code should be
# checked out when reviews are done
PROJECT_DIR = './'
