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

    if 'LINTREVIEW_SETTINGS' not in os.environ:
        msg = ("Unable to load configuration file. Please set "
               "LINTREVIEW_SETTINGS in your environment before running.")
        raise ImportError(msg)
    config.from_envvar('LINTREVIEW_SETTINGS')
    if config.get('LOGGING_CONFIG'):
        logging.config.fileConfig(config.get('LOGGING_CONFIG'))

    return config


class ReviewConfig(object):
    """
    Provides a domain level API to a repositories
    .lintrc file. Allows reading tool names and tool configuration
    """

    def __init__(self, lintrc):
        self._config = ConfigParser()
        self._config.readfp(StringIO(lintrc))

    def linters(self):
        try:
            values = self._config.get('tools', 'linters')
            return map(lambda x: x.strip(), values.split(','))
        except:
            return None

    def linter_config(self, tool):
        tool_name = 'tool_' + tool
        try:
            config = self._config.items(tool_name)
            return dict(config)
        except:
            return None
