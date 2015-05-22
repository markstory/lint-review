import logging
import os
from lintreview.tools import Tool
from lintreview.tools import run_command
from lintreview.utils import in_path
from lintreview.utils import npm_exists

log = logging.getLogger(__name__)


class Jscs(Tool):

    name = 'jscs'

    def check_dependencies(self):
        """
        See if jscs is on the system path.
        """
        return in_path('jscs') or npm_exists('jscs')

    def match_file(self, filename):
        base = os.path.basename(filename)
        name, ext = os.path.splitext(base)
        return ext == '.js'

    def process_files(self, files):
        """
        Run code checks with jscs.
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
        cmd = 'jscs'
        if npm_exists('jscs'):
            cmd = os.path.join(os.getcwd(), 'node_modules', '.bin', 'jscs')
        command = [cmd, '--reporter=checkstyle']
        # Add config file if its present
        if self.options.get('config'):
            command += ['--config', self.apply_base(self.options['config'])]
        else:
            command += ['--preset', self.options.get('preset', 'google')]
        command += files
        return command
