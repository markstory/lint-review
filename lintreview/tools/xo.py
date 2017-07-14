import functools
import logging
import os
from lintreview.tools import Tool, run_command, process_checkstyle
from lintreview.utils import in_path, npm_exists

log = logging.getLogger(__name__)


class Xo(Tool):

    name = 'xo'

    def check_dependencies(self):
        """
        See if XO is on the system path.
        """
        return in_path('xo') or npm_exists('xo')

    def match_file(self, filename):
        """
        Check if a file should be linted using XO.
        """
        base = os.path.basename(filename)
        name, ext = os.path.splitext(base)
        return ext == '.js' or ext == '.jsx'

    def process_files(self, files):
        """
        Run code checks with XO.
        """
        log.debug('Processing %s files with %s', files, self.name)
        cmd = self.name
        if npm_exists('xo'):
            cmd = os.path.join(os.getcwd(), 'node_modules', '.bin', 'xo')
        command = [cmd, '--reporter', 'checkstyle']

        command += files
        output = run_command(command, ignore_error=True)
        self._process_output(output, files)

    def _process_output(self, output, files):
        filename_converter = functools.partial(
            self._relativize_filename,
            files)
        process_checkstyle(self.problems, output, filename_converter)
