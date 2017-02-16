import functools
import logging
import os
from lintreview.tools import Tool, run_command, process_quickfix
from lintreview.utils import in_path, npm_exists

log = logging.getLogger(__name__)


class Standardjs(Tool):

    name = 'standardjs'

    def check_dependencies(self):
        """
        See if standard is on the system path.
        """
        return in_path('standard') or npm_exists('standard')

    def match_file(self, filename):
        """
        Check if a file should be linted using standard.
        """
        base = os.path.basename(filename)
        name, ext = os.path.splitext(base)
        return ext == '.js'

    def process_files(self, files):
        """
        Run code checks with standard.
        """
        log.debug('Processing %s files with %s', files, self.name)
        cmd = self.name
        if npm_exists('standard'):
            cmd = os.path.join(os.getcwd(), 'node_modules', '.bin', 'standard')

        filename_converter = functools.partial(
            self._relativize_filename,
            files)

        command = [cmd] + list(files)
        output = run_command(
            command,
            split=True,
            ignore_error=True)

        output = filter(lambda line: not line.startswith('standard'),
                        output)
        process_quickfix(self.problems, output, filename_converter)
