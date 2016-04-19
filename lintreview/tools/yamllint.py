import os
import logging
from lintreview.tools import Tool
from lintreview.tools import run_command
from lintreview.utils import in_path

log = logging.getLogger(__name__)


class Yamllint(Tool):

    name = 'yamllint'

    def check_dependencies(self):
        """
        See if yamllint is on the PATH
        """
        return in_path('yamllint')

    def match_file(self, filename):
        base = os.path.basename(filename)
        name, ext = os.path.splitext(base)
        return ext in ['.yml', '.yaml']

    def process_files(self, files):
        """
        Run code checks with yamllint.
        Only a single process is made for all files
        to save resources.
        Configuration is not supported at this time
        """
        log.debug('Processing %s files with %s', files, self.name)

        command = ['yamllint', '--format=parsable']
        command += files

        output = run_command(command, split=True, ignore_error=True)
        if not output:
            log.debug('No yamllint errors found.')
            return False

        for line in output:
            filename, line, error = self._parse_line(line)
            self.problems.add(filename, line, error)

    def _parse_line(self, line):
        """
        yamllint only generates results as stdout.
        Parse the output for real data.
        """
        parts = line.split(':', 3)
        if len(parts) == 3:
            message = parts[2].strip()
        else:
            message = parts[3].strip()
        return (parts[0], int(parts[1]), message)
