import logging
import os
from lintreview.tools import Tool
from lintreview.tools import run_command
from lintreview.utils import in_path
from lintreview.utils import npm_exists

log = logging.getLogger(__name__)


class Jshint(Tool):

    name = 'jshint'

    def check_dependencies(self):
        """
        See if jshint is on the system path.
        """
        return in_path('jshint') or npm_exists('jshint')

    def match_file(self, filename):
        base = os.path.basename(filename)
        name, ext = os.path.splitext(base)
        return ext == '.js'

    def process_files(self, files):
        """
        Run code checks with jshint.
        Only a single process is made for all files
        to save resources.
        """
        log.debug('Processing %s files with %s', files, self.name)
        command = self.create_command(files)
        output = run_command(
            command,
            ignore_error=True)
        self._process_checkstyle(output)

    def create_command(self, files):
        cmd = 'jshint'
        if npm_exists('jshint'):
            cmd = os.path.join(os.getcwd(), 'node_modules', '.bin', 'jshint')
        command = [cmd, '--checkstyle-reporter']
        # Add config file if its present
        if self.options.get('config'):
            command += ['--config', self.apply_base(self.options['config'])]
        command += files
        return command
