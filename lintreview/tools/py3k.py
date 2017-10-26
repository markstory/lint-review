from __future__ import absolute_import
import os
import logging
import functools
from lintreview.tools import Tool, run_command, process_quickfix
from lintreview.utils import in_path

log = logging.getLogger(__name__)


class Py3k(Tool):
    """
    $ pylint --py3k is a special mode for porting to python 3 which
    disables other pylint checkers.
    see https://github.com/PyCQA/pylint/issues/761
    """

    name = 'py3k'

    def check_dependencies(self):
        """
        See if pylint is on the PATH
        """
        return in_path('pylint')

    def match_file(self, filename):
        base = os.path.basename(filename)
        name, ext = os.path.splitext(base)
        return ext == '.py'

    def process_files(self, files):
        """
        Run code checks with pylint --py3k.
        Only a single process is made for all files
        to save resources.
        """
        log.debug('Processing %s files with %s', files, self.name)
        command = self.make_command(files)
        output = run_command(command, split=True, ignore_error=True)
        if not output:
            log.debug('No py3k errors found.')
            return False

        output = [line for line in output if not line.startswith("*********")]

        filename_converter = functools.partial(
            self._relativize_filename,
            files)
        process_quickfix(self.problems, output, filename_converter)

    def make_command(self, files):
        msg_template = '{path}:{line}:{column}:{msg_id} {msg}'
        command = [
            'pylint',
            '--py3k',
            '--reports=n',
            '--msg-template',
            msg_template,
        ]
        for option in self.options:
            log.warning('Set non-existent py3k option: %s', option)
        command.extend(files)
        return command
