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
            else:
                log.error('%s is not a valid option to credo', option)
        command += files
        output = docker.run('credo', command, self.base_path)
        if not output:
            log.debug('No credo errors found.')
            return False

        output = map(self.transform_flycheck_range, output.strip().splitlines())
        process_quickfix(self.problems, output, docker.strip_base)

    def transform_flycheck_range(self, message):
        """
        Flycheck format can have a range (filename:start:end:message).
        We don't care about the end anyway, so we remove it if present.
        """
        parts = message.split(':')
        if len(parts) <= 3:
            return message
        try:
            int(parts[2])
            parts.pop(2)
            return ':'.join(parts)
        except ValueError:
            return message

    def parse_ini_bool(self, string):
        true = ['1', 'yes', 'true', 'on']
        return string.lower() in true
