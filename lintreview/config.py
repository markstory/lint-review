import os
import logging.config

from flask.config import Config
from ConfigParser import ConfigParser
from StringIO import StringIO


def load_config():
    """
    Loads the config files merging the defaults
    with the file defined in environ.LINTREVIEW_SETTINGS if it exists.
    """
    config = Config(os.getcwd())

    if 'LINTREVIEW_SETTINGS' in os.environ:
        config.from_envvar('LINTREVIEW_SETTINGS')
    elif os.path.exists(os.path.join(os.getcwd(), 'settings.py')):
        config.from_pyfile('settings.py')
    else:
        msg = ("Unable to load configuration file. Please "
               "either create ./settings.py or set LINTREVIEW_SETTINGS "
               "in your environment before running.")
        raise ImportError(msg)
    if config.get('LOGGING_CONFIG'):
        logging.config.fileConfig(
            config.get('LOGGING_CONFIG'),
            disable_existing_loggers=False)

    if config.get('SSL_CA_BUNDLE'):
        os.environ['REQUESTS_CA_BUNDLE'] = config.get('SSL_CA_BUNDLE')

    return config


def get_lintrc_defaults(config):
    """
    Load the default lintrc, if it exists
    """
    if config.get('LINTRC_DEFAULTS'):
        with open(config.get('LINTRC_DEFAULTS')) as f:
            return f.read()


class ReviewConfig(object):
    """
    Provides a domain level API to a repositories
    .lintrc file. Allows reading tool names and tool configuration
    """

    def __init__(self, lintrc, lintrc_defaults=None):
        self._config = ConfigParser()
        if lintrc_defaults:
            self._config.readfp(StringIO(lintrc_defaults))
        self._config.readfp(StringIO(lintrc))

    def linters(self):
        try:
            values = self._config.get('tools', 'linters')
            return map(lambda x: x.strip(), values.split(','))
        except:
            return []

    def linter_config(self, tool):
        tool_name = 'tool_' + tool
        try:
            config = self._config.items(tool_name)
            return dict(config)
        except:
            return []

    def ignore_patterns(self):
        try:
            value = self._config.get('files', 'ignore')
            patterns = map(lambda x: x.strip(), value.split("\n"))
            return patterns
        except:
            return []

    def ignore_branches(self):
        try:
            values = self._config.get('branches', 'ignore')
            return map(lambda x: x.strip(), values.split(','))
        except:
            return []
