import functools
import logging
import os
from lintreview.tools import Tool
from lintreview.tools import run_command
from lintreview.utils import in_path
from lintreview.utils import npm_exists


log = logging.getLogger(__name__)


class Sasslint(Tool):

    name = 'sasslint'

    def check_dependencies(self):
        """
        See if sass-lint is on the system path.
        """
        return in_path('sass-lint') or npm_exists('sass-lint')

    def match_file(self, filename):
        base = os.path.basename(filename)
        name, ext = os.path.splitext(base)
        return ext == '.sass' or ext == '.scss'

    def process_files(self, files):
        """
        Run code checks with sass-lint.
        Only a single process is made for all files
        to save resources.
        """
        log.debug('Processing %s files with %s', files, self.name)
        cmd = 'sass-lint'
        if npm_exists('sass-lint'):
            cmd = os.path.join(
                os.getcwd(),
                'node_modules',
                '.bin',
                'sass-lint')
        command = [cmd, '-f', 'checkstyle', '-v']
        command += files
        if self.options.get('ignore'):
            command += ['--ignore ', self.options.get('ignore')]
        if self.options.get('config'):
            command += ['--config', self.apply_base(self.options['config'])]
        output = run_command(
            command,
            ignore_error=True)
        filename_converter = functools.partial(
            self._relativize_filename,
            files)
        self._process_checkstyle(output, filename_converter)
