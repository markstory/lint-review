from __future__ import absolute_import
import os
import logging
from lintreview.tools import Tool, run_command, process_quickfix
from lintreview.utils import in_path

log = logging.getLogger(__name__)


class Pep8(Tool):

    name = 'pep8'

    def check_dependencies(self):
        """
        See if pep8 is on the PATH
        """
        return in_path('pep8')

    def match_file(self, filename):
        base = os.path.basename(filename)
        name, ext = os.path.splitext(base)
        return ext == '.py'

    def process_files(self, files):
        """
        Run code checks with pep8.
        Only a single process is made for all files
        to save resources.
        """
        log.debug('Processing %s files with %s', files, self.name)
        pep8_options = ['exclude',
                        'filename',
                        'select',
                        'ignore',
                        'max-line-length']
        command = ['pep8', '-r']
        for option, value in self.options.items():
            if option in pep8_options:
                command += [u'--{}'.format(option), value]
            else:
                log.error('%s is not a valid option to pep8', option)
        command += files
        output = run_command(command, split=True, ignore_error=True)
        if not output:
            log.debug('No pep8 errors found.')
            return False

        process_quickfix(self.problems, output, lambda name: name)
