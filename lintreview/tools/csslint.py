import functools
import logging
import os
from lintreview.tools import Tool
from lintreview.tools import run_command
from lintreview.utils import in_path
from lintreview.utils import npm_exists


log = logging.getLogger(__name__)


class Csslint(Tool):

    name = 'csslint'

    def check_dependencies(self):
        """
        See if csslint is on the system path.
        """
        return in_path('csslint') or npm_exists('csslint')

    def match_file(self, filename):
        base = os.path.basename(filename)
        name, ext = os.path.splitext(base)
        return ext == '.css'

    def process_files(self, files):
        """
        Run code checks with csslint.
        Only a single process is made for all files
        to save resources.
        """
        log.debug('Processing %s files with %s', files, self.name)
        cmd = 'csslint'
        if npm_exists('csslint'):
            cmd = os.path.join(os.getcwd(), 'node_modules', '.bin', 'csslint')
        command = [cmd, '--format=checkstyle-xml']

        if self.options.get('ignore'):
            command += ['--ignore=' + self.options.get('ignore')]
        command += files
        output = run_command(
            command,
            ignore_error=True)
        filename_converter = functools.partial(
            self._relativize_filename,
            files)
        self._process_checkstyle(output, filename_converter)
