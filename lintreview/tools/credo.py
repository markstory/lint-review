from __future__ import absolute_import
import os
import logging
import lintreview.docker as docker
from lintreview.tools import Tool, process_quickfix

log = logging.getLogger(__name__)


class Credo(Tool):
    """
    Run credo on files.
    """

    name = 'credo'

    def check_dependencies(self):
        """
        See if credo image exists
        """
        return docker.image_exists('credo')

    def match_file(self, filename):
        base = os.path.basename(filename)
        name, ext = os.path.splitext(base)
        return ext in ('.ex', '.exs')

    def process_files(self, files):
        """
        Run code checks with credo.
        """
        log.debug('Processing %s files with %s', files, self.name)
        command = self.create_command()
        command += files
        output = docker.run('credo', command, self.base_path)
        if not output:
            log.debug('No credo errors found.')
            return False

        process_quickfix(
            self.problems,
            output.strip().splitlines(),
            docker.strip_base,
            columns=4)

    def create_command(self):
        credo_options = ['checks',
                         'config-name',
                         'ignore-checks']
        credo_flags = ['all',
                       'all-priorities',
                       'strict']
        command = ['mix', 'credo', 'list', '--format', 'flycheck']
        for option, value in self.options.items():
            if option in credo_options:
                command += [u'--{}'.format(option), value]
            elif option in credo_flags:
                if self.parse_ini_bool(value):
                    command += [u'--{}'.format(option)]
        return command

    def parse_ini_bool(self, value):
        if isinstance(value, bool):
            return value
        if isinstance(value, int):
            return True if value == 1 else False
        true = ['1', 'yes', 'true', 'on']
        return value.lower() in true
