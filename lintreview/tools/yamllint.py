from __future__ import absolute_import
import os
import logging
from lintreview.tools import Tool, run_command, process_quickfix
from lintreview.utils import in_path

log = logging.getLogger(__name__)


class Yamllint(Tool):

    name = 'yamllint'

    def check_dependencies(self):
        """
        See if yamllint is on the PATH
        """
        return in_path('yamllint')

    def match_file(self, filename):
        base = os.path.basename(filename)
        name, ext = os.path.splitext(base)
        return ext in ['.yml', '.yaml']

    def process_files(self, files):
        """
        Run code checks with yamllint.
        Only a single process is made for all files
        to save resources.
        Configuration is not supported at this time
        """
        log.debug('Processing %s files with %s', files, self.name)

        command = ['yamllint', '--format=parsable']
        # Add config file if its present
        if self.options.get('config'):
            command += ['-c', self.apply_base(self.options['config'])]
        command += files

        output = run_command(command, split=True, ignore_error=True)
        if not output:
            log.debug('No yamllint errors found.')
            return False

        process_quickfix(self.problems, output, lambda x: x)
