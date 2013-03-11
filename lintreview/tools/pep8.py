import os
import logging
from lintreview.tools import Tool
from lintreview.tools import run_command
from lintreview.utils import in_path

log = logging.getLogger(__name__)


class Pep8(Tool):

    name = 'pep8'

    def check_dependencies(self):
        """
        See if pep8 is on the PATH
        """
        return in_path('pep8')

    def match_file(self, filename):
        base = os.path.basename(filename)
        name, ext = os.path.splitext(base)
        return ext == '.py'

    def process_files(self, files):
        """
        Run code checks with pep8.
        Only a single process is made for all files
        to save resources.
        """
        log.debug('Processing %s files with %s', files, self.name)
        command = ['pep8', '-r']
        if self.options.get('ignore'):
            command += ['--ignore', self.options.get('ignore')]
        command += files
        output = run_command(command, split=True, ignore_error=True)
        if not output:
            log.debug('No pep8 errors found.')
            return False

        for line in output:
            filename, line, error = self._parse_line(line)
            self.problems.add(filename, line, error)

    def _parse_line(self, line):
        """
        pep8 only generates results as stdout.
        Parse the output for real data.
        """
        parts = line.split(':', 3)
        message = parts[3].strip()
        return (parts[0], int(parts[1]), message)
