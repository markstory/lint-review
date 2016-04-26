import os
import logging
from lintreview.tools import Tool
from lintreview.tools import run_command
from lintreview.utils import in_path

log = logging.getLogger(__name__)


class Jsonlint(Tool):

    name = 'jsonlint'

    def check_dependencies(self):
        """
        See if jsonlint is on the PATH
        """
        return in_path('jsonlint')

    def match_file(self, filename):
        base = os.path.basename(filename)
        name, ext = os.path.splitext(base)
        return ext == '.json'

    def process_files(self, files):
        """
        Run code checks with jsonlint.
        Only a single process is made for all files
        to save resources.
        Configuration is not supported at this time
        """
        log.debug('Processing %s files with %s', files, self.name)

        command = ['jsonlint']
        command += files

        output = run_command(command, split=True, ignore_error=True)
        if not output:
            log.debug('No jsonlint errors found.')
            return False

        for line in output:
            if (line[0] == ' ' or
                    line.find(': has errors') >= 0 or
                    line.find(': ok') >= 0):
                continue
            filename, line, error = self._parse_line(line)
            self.problems.add(filename, line, error)

    def _parse_line(self, line):
        """
        jsonlint only generates results as stdout.
        Parse the output for real data.
        """
        parts = line.split(':', 3)
        return (parts[0], int(parts[1]), parts[3][1:-1])
