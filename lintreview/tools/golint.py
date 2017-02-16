import logging
import os
import functools
from lintreview.tools import Tool, run_command, process_quickfix
from lintreview.utils import in_path, go_bin_path

log = logging.getLogger(__name__)


class Golint(Tool):
    """
    Run golint on files. This may need to offer config options
    to map packages -> dirs so we can run golint once per package.
    """

    name = 'golint'

    def check_dependencies(self):
        """
        See if golint is on the system path.
        """
        return in_path('golint') or go_bin_path('golint')

    def match_file(self, filename):
        base = os.path.basename(filename)
        name, ext = os.path.splitext(base)
        return ext == '.go'

    def process_files(self, files):
        """
        Run code checks with golint.
        Only a single process is made for all files
        to save resources.
        """
        command = self.create_command(files)
        output = run_command(
            command,
            ignore_error=True,
            split=True)
        filename_converter = functools.partial(
            self._relativize_filename,
            files)
        # Look for multi-package error message, and re-run tools
        if len(output) == 1 and 'is in package' in output[0]:
            log.info('Re-running golint on individual files'
                     'as diff contains files from multiple packages: %s',
                     output[0])
            self.run_individual_files(files, filename_converter)
        else:
            process_quickfix(self.problems, output, filename_converter)

    def create_command(self, files):
        command = ['golint']
        if go_bin_path('golint'):
            command = [go_bin_path('golint')]
        if 'min_confidence' in self.options:
            command += ['-min_confidence', self.options.get('min_confidence')]
        command += files
        return command

    def run_individual_files(self, files, filename_converter):
        """
        If we get an error from golint about different packages
        we have to re-run golint on each file as figuring out package
        relations is hard.
        """
        for filename in files:
            command = self.create_command([filename])
            output = run_command(command, ignore_error=True, split=True)
            process_quickfix(self.problems, output, filename_converter)
