# Basic flask config
DEBUG = True
TESTING = True

SERVER_NAME = 'lint.example.com'

WORKSPACE = './workspace'

# Use GITHUB_URL when working with github:e
# When working with github:e don't forget to add the /api/v3/ path
GITHUB_URL = 'https://api.github.com/'

# Github username + password
# This is the user that lintreview will use
# to fetch repositories and leave review comments.
GITHUB_USER = 'octocat'
GITHUB_PASSWORD = ''

# Path where project code should be
# checked out when reviews are done
PROJECT_DIR = './'
