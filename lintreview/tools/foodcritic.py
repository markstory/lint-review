import os
import logging

from lintreview.tools import Tool
from lintreview.tools import run_command
from lintreview.utils import in_path
from lintreview.utils import bundle_exists

log = logging.getLogger(__name__)


class Foodcritic(Tool):

    name = 'foodcritic'

    def check_dependencies(self):
        """
        See if foodcritic is on the PATH
        """
        return in_path('foodcritic') or bundle_exists('foodcritic')

    def process_files(self, files):
        command = ['foodcritic']
        if bundle_exists('foodcritic'):
            command = ['bundle', 'exec', 'foodcritic']
        # if no directory is set, assume the root
        path = os.path.join(self.base_path, self.options.get('path', ''))
        command += [path]
        output = run_command(command, split=True, ignore_error=False)

        if output[0] == '\n':
            log.debug('No foodcritic errors found.')
            return False

        for line in output:
            filename, line, error = self._parse_line(line)
            self.problems.add(filename, line, error)

    def _parse_line(self, line):
        """
        foodcritic only generates results as stdout.
        Parse the output for real data.
        """
        log.debug('Line: %s' % line)
        parts = line.split(': ')
        filename = parts[2].split(':')[0].strip()
        line = int(parts[2].split(':')[1])
        message = ': '.join(parts[:2]).strip()
        return (filename, line, message)
