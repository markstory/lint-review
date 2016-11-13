import os
import logging
from lintreview.tools import Tool
from lintreview.tools import run_command
from lintreview.utils import in_path

log = logging.getLogger(__name__)


class Ansible(Tool):

    name = 'ansible'

    def check_dependencies(self):
        """
        See if ansible-lint is on the PATH
        """
        return in_path('ansible-lint')

    def match_file(self, filename):
        base = os.path.basename(filename)
        name, ext = os.path.splitext(base)
        return ext == '.yml'

    def process_files(self, files):
        """
        Run code checks with ansible-lint.
        Only a single process is made for all files
        to save resources.
        """
        log.debug('Processing %s files with %s', files, self.name)
        command = ['ansible-lint', '-p']
        if self.options.get('ignore'):
            command += ['-x', self.options.get('ignore')]
        command += files
        output = run_command(command, split=True, ignore_error=True)
        if not output:
            log.debug('No ansible-lint errors found.')
            return False

        output.sort()

        for line in output:
            filename, line, error = self._parse_line(line)
            self.problems.add(filename, line, error)

    def _parse_line(self, line):
        """
        ansible-lint only generates results as stdout.
        Parse the output for real data.
        """
        parts = line.split(':')
        message = parts[2].strip()
        return (parts[0], int(parts[1]), message)
