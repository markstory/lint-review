import os
import logging
from lintreview.tools import Tool
from lintreview.tools import run_command
from lintreview.utils import in_path
from lintreview.utils import bundle_exists

log = logging.getLogger(__name__)


class Rubocop(Tool):

    name = 'rubocop'

    def check_dependencies(self):
        """
        See if rubocop is on the PATH
        """
        return in_path('rubocop') or bundle_exists('rubocop')

    def match_file(self, filename):
        base = os.path.basename(filename)
        name, ext = os.path.splitext(base)
        return ext == '.rb'

    def process_files(self, files):
        """
        Run code checks with rubocop
        """
        log.debug('Processing %s files with %s', files, self.name)
        command = ['rubocop']
        if bundle_exists('rubocop'):
            command = ['bundle', 'exec', 'rubocop']
        command += ['--format', 'emacs']
        if self.options.get('display_cop_names', '').lower() == 'true':
            command += ['--display-cop-names']
        command += files
        output = run_command(
            command,
            split=True,
            ignore_error=True,
            include_errors=False
        )

        if not output:
            log.debug('No rubocop errors found.')
            return False

        for line in output:
            filename, line, error = self._parse_line(line)
            self.problems.add(filename, line, error)

    def _parse_line(self, line):
        """
        `rubocop --format emacs` lines look like this:
        filename:lineno:charno: error-type: error
        """
        parts = line.split(':', 3)
        message = parts[3].strip()
        return (parts[0], int(parts[1]), message)
