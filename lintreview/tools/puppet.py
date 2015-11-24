import os
import logging
from lintreview.tools import Tool
from lintreview.tools import run_command
from lintreview.utils import in_path
from lintreview.utils import bundle_exists

log = logging.getLogger(__name__)


class Puppet(Tool):

    name = 'puppet-lint'

    def check_dependencies(self):
        """
        See if puppet-lint is on the PATH
        """
        return in_path('puppet-lint') or bundle_exists('puppet-lint')

    def match_file(self, filename):
        base = os.path.basename(filename)
        name, ext = os.path.splitext(base)
        return ext == '.pp'

    def process_files(self, files):
        """
        Run code checks with puppet-lint
        """
        log.debug('Processing %s files with %s', files, self.name)
        command = ['puppet-lint']
        if bundle_exists('puppet-lint'):
            command = ['bundle', 'exec', 'puppet-lint']
        command += ['--log-format',
                    '%{path}:%{linenumber}:%{KIND}:%{message}']
        command += files
        output = run_command(
            command,
            split=True,
            ignore_error=True,
            include_errors=False
        )

        if not output:
            log.debug('No puppet-lint errors found.')
            return False

        for line in output:
            filename, line, error = self._parse_line(line)
            self.problems.add(filename, line, error)

    def _parse_line(self, line):
        """
        `rubocop --format emacs` lines look like this:
        filename:lineno:charno: error-type: error
        """
        parts = line.split(':', 2)
        message = parts[2].strip()
        filename = os.path.abspath(parts[0])
        return (filename, int(parts[1]), message)
