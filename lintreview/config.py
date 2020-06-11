import os
import logging.config

from flask.config import Config
from configparser import ConfigParser
from io import StringIO


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
    config = ReviewConfig(app_config)
    if app_config:
        defaults = get_lintrc_defaults(app_config)
        if defaults:
            config.load_ini(defaults)
    config.load_ini(ini_config)
    return config


def comma_value(values):
    return [x.strip() for x in values.split(',')]


def newline_value(values):
    return [x.strip() for x in values.split('\n')]


def boolean_value(value):
    if value in ('yes', 'y', 1, '1', True, 'True', 'true'):
        return True
    if value in ('no', 'n', 0, '0', False, 'False', 'false'):
        return False
    raise ValueError(u'Could not convert `{}` to a boolean'.format(value))


class ReviewConfig(object):
    """
    Provides a domain level API to a application
    and repository configuration data.
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
        for key, value in data.items():
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
        for linter, tool_config in linter_config.items():
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
            return list(self._data['linters'].keys())
        except Exception:
            return []

    def linter_config(self, tool):
        try:
            return self._data['linters'][tool]
        except Exception:
            return {}

    def fixers_enabled(self):
        try:
            return bool(self._data['fixers']['enable'])
        except Exception:
            return False

    def fixer_workflow(self):
        try:
            return self._data['fixers']['workflow']
        except Exception:
            return 'commit'

    def ignore_patterns(self):
        try:
            return self._data['files']['ignore']
        except Exception:
            return []

    def ignore_branches(self):
        try:
            return self._data['branches']['ignore']
        except Exception:
            return []

    def summary_threshold(self):
        """Get the threshold at which 1 single summary comment is posted.
        """
        if 'review' in self._data:
            try:
                return int(self._data['review']['summary_comment_threshold'])
            except Exception:
                pass
        try:
            return int(self._data['SUMMARY_THRESHOLD'])
        except Exception:
            return None

    def passed_review_label(self):
        """Get the label name that is managed by review publishing
        """
        if 'review' in self._data:
            try:
                return self._data['review']['apply_label_on_pass']
            except KeyError:
                pass
        try:
            return self._data['OK_LABEL']
        except KeyError:
            return None

    def failed_review_status(self):
        """Get the status name to use for failed reviews
        """
        if 'review' in self._data:
            try:
                value = boolean_value(self._data['review']['fail_on_comments'])

                return 'failure' if value else 'success'
            except Exception:
                pass
        if 'PULLREQUEST_STATUS' in self._data:
            value = boolean_value(self._data['PULLREQUEST_STATUS'])
            return 'failure' if value else 'success'
        return 'failure'

    def get(self, key, default=None):
        """Dict compatibility accessor for application config data
        """
        if key not in self._data:
            return default
        return self._data[key]

    def __getitem__(self, key):
        """Dict compatibility method
        """
        if key not in self._data:
            raise KeyError(key + " is invalid")
        return self._data[key]

    def load_ini(self, ini_config):
        """
        Read the provided ini contents arguments and merge
        the data in the ini config into the config object.

        ini_config is assumed to be a string of the ini file contents.
        """
        parser = ConfigParser()
        parser.read_file(StringIO(ini_config))
        data = {
            'linters': {},
            'files': {},
            'branches': {},
            'fixers': {},
            'review': {}
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

        if parser.has_section('fixers'):
            data['fixers'] = dict(parser.items('fixers'))
        if parser.has_section('review'):
            data['review'] = dict(parser.items('review'))
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
