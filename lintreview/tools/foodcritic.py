from __future__ import absolute_import
import logging
import lintreview.docker as docker

from lintreview.tools import Tool

log = logging.getLogger(__name__)


class Foodcritic(Tool):

    name = 'foodcritic'

    def check_dependencies(self):
        """
        See if foodcritic is on the PATH
        """
        return docker.image_exists('ruby2')

    def process_files(self, files):
        command = ['foodcritic', '--no-progress']

        # if no directory is set, assume the root
        path = self.options.get('path', '')
        path = docker.apply_base(path)

        command.append(path)
        output = docker.run('ruby2', command, self.base_path)

        if output[0] == '\n':
            log.debug('No foodcritic errors found.')
            return False

        for line in output.split("\n"):
            if len(line.strip()) == 0:
                return
            filename, line, error = self._parse_line(line)
            self.problems.add(filename, line, error)

    def _parse_line(self, line):
        """
        foodcritic only generates results as stdout.
        Parse the output for real data.
        """
        log.debug('Line: %s' % line)
        parts = line.split(': ')

        filename = parts[2].split(':')[0].strip()
        filename = docker.strip_base(filename)

        line = int(parts[2].split(':')[1])
        message = ': '.join(parts[:2]).strip()
        return (filename, line, message)
