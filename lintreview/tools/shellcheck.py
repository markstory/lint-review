import logging
import os
import functools
from lintreview.tools import Tool, run_command, process_checkstyle
from lintreview.utils import in_path

log = logging.getLogger(__name__)


class Shellcheck(Tool):

    name = 'shellcheck'

    def check_dependencies(self):
        """
        See if shellcheck is on the system path.
        """
        return in_path('shellcheck')

    def match_file(self, filename):
        base = os.path.basename(filename)
        name, ext = os.path.splitext(base)
        if ext in ('.sh', '.bash', '.ksh', '.zsh'):
            return True

        if not os.path.exists(filename) or not os.access(filename, os.X_OK):
            return False

        # Check for a shebang in the first line.
        with open(filename, 'r') as f:
            line = f.readline()
            return line.startswith('#!') and (
                'bash' in line or
                'sh' in line or
                'zsh' in line or
                'ksh' in line
            )

    def process_files(self, files):
        """
        Run code checks with shellcheck.
        """
        log.debug('Processing %s files with %s', files, self.name)
        command = self.create_command(files)
        output = run_command(
            command,
            ignore_error=True,
            include_errors=False)
        filename_converter = functools.partial(
            self._relativize_filename,
            files)
        process_checkstyle(self.problems, output, filename_converter)
        map(self.escape_backtick, self.problems)

    def escape_backtick(self, problem):
        problem.body = problem.body.replace('`', '\`')

    def create_command(self, files):
        command = ['shellcheck']
        command += ['--format=checkstyle']
        shell = 'sh'
        if self.options.get('shell'):
            shell = self.apply_base(self.options['shell'])
        command += ['--shell=' + shell]
        if self.options.get('exclude'):
            command += ['--exclude=' + str(self.options['exclude'])]
        command += files
        return command
