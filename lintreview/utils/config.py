from ConfigParser import ConfigParser
from StringIO import StringIO


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
            return []

    def linter_config(self, tool):
        tool_name = 'tool_' + tool
        try:
            config = self._config.items(tool_name)
            return dict(config)
        except:
            return {}
