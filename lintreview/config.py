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


def build_review_config(ini_config, app_config=None):
    """
    Build a new ReviewConfig object using the ini config file
    and the defaults if they exist in the app_config
    """
    config = ReviewConfig()
    if app_config:
        defaults = get_lintrc_defaults(app_config)
        if defaults:
            config.load_ini(defaults)
    config.load_ini(ini_config)
    return config


def comma_value(values):
    return map(lambda x: x.strip(), values.split(','))


def newline_value(values):
    return map(lambda x: x.strip(), values.split('\n'))


class ReviewConfig(object):
    """
    Provides a domain level API to a repositories
    .lintrc file. Allows reading tool names and tool configuration
    """
    def __init__(self, data=None):
        self._data = {}
        if data:
            self._data = data

    def update(self, data):
        """
        Does a shallow merge of configuration settings.
        This allows repos to control entire tool config by only
        defining the keys they want. If we did a recursive merge, the
        user config file would have to 'undo' our default file changes.

        The one exception is that if the new data has
        empty config, and the current data has non-empty config, the
        non-empty config will be retained.
        """
        for key, value in data.iteritems():
            if key == 'linters' and 'linters' in self._data:
                self._update_linter_config(value)
            else:
                self._data[key] = value

    def _update_linter_config(self, linter_config):
        """
        Update linter config.

        Because linter config is a nested structure, it needs to be
        updated in a somewhat recursive way.
        """
        for linter, tool_config in linter_config.iteritems():
            if self._config_update(linter, tool_config):
                self._data['linters'][linter] = tool_config

    def _config_update(self, linter, tool_config):
        if linter not in self.linters():
            return True
        existing = self.linter_config(linter)
        if tool_config == {} and existing != {}:
            return False
        return True

    def linters(self):
        try:
            return self._data['linters'].keys()
        except:
            return []

    def linter_config(self, tool):
        try:
            return self._data['linters'][tool]
        except:
            return {}

    def ignore_patterns(self):
        try:
            return self._data['files']['ignore']
        except:
            return []

    def ignore_branches(self):
        try:
            return self._data['branches']['ignore']
        except:
            return []

    def load_ini(self, ini_config):
        """
        Read the provided ini contents arguments and merge
        the data in the ini config into the config object.

        ini_config is assumed to be a string of the ini file contents.
        """
        parser = ConfigParser()
        parser.readfp(StringIO(ini_config))
        data = {
            'linters': {},
            'files': {},
            'branches': {},
        }
        if parser.has_section('files'):
            ignore = parser.get('files', 'ignore')
            data['files']['ignore'] = newline_value(ignore)
        if parser.has_section('branches'):
            ignore = parser.get('branches', 'ignore')
            data['branches']['ignore'] = comma_value(ignore)

        linters = []
        if parser.has_section('tools'):
            linters = comma_value(parser.get('tools', 'linters'))
        # Setup empty config sections
        for linter in linters:
            data['linters'][linter] = {}
        for section in parser.sections():
            if not section.startswith('tool_'):
                continue
            # Strip off tool_
            linter = section[5:]
            data['linters'][linter] = dict(parser.items(section))
        self.update(data)
