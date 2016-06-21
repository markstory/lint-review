import logging
import os
import functools
from lintreview.tools import Tool
from lintreview.tools import run_command
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
        return ext == '.sh'

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
        self._process_checkstyle(output, filename_converter)

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
