from __future__ import absolute_import
import logging
import os
import functools
from lintreview.tools import Tool, run_command, process_quickfix
from lintreview.utils import in_path

log = logging.getLogger(__name__)


class Luacheck(Tool):

    name = 'luacheck'

    def check_dependencies(self):
        """
        See if luacheck is on the system path.
        """
        return in_path('luacheck')

    def match_file(self, filename):
        base = os.path.basename(filename)
        name, ext = os.path.splitext(base)
        return ext == '.lua'

    def process_files(self, files):
        """
        Run code checks with luacheck.
        """
        log.debug('Processing %s files with %s', files, self.name)
        command = self.create_command(files)
        output = run_command(
            command,
            ignore_error=True,
            split=True)
        filename_converter = functools.partial(
            self._relativize_filename,
            files)
        process_quickfix(self.problems, output, filename_converter)

    def escape_backtick(self, problem):
        problem.body = problem.body.replace('`', '\`')

    def create_command(self, files):
        command = ['luacheck']
        command += ['--formatter=plain']
        command += ['--codes']
        if self.options.get('config'):
            command += ['--config', self.apply_base(self.options['config'])]
        command += files
        return command
