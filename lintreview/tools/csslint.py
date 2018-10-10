from __future__ import absolute_import
import logging
import os
import re
import lintreview.docker as docker
from lintreview.tools import Tool


log = logging.getLogger(__name__)


class Csslint(Tool):

    name = 'csslint'

    def check_dependencies(self):
        """
        See if nodejs image exists.
        """
        return docker.image_exists('nodejs')

    def match_file(self, filename):
        base = os.path.basename(filename)
        name, ext = os.path.splitext(base)
        return ext == '.css'

    def process_files(self, files):
        """
        Run code checks with csslint.
        Only a single process is made for all files
        to save resources.
        """
        log.debug('Processing %s files with %s', files, self.name)
        cmd = 'csslint'
        command = [cmd, '--format=compact']

        if self.options.get('ignore'):
            command += ['--ignore=' + self.options.get('ignore')]
        command += files

        output = docker.run(
            'nodejs',
            command,
            source_dir=self.base_path)
        self._process_output(output)

    def _process_output(self, output):
        """The checkstyle output from csslint is not
        reliable for large results so we use compact format which looks like:

        <filepath>: line 1 col 1, <message>
        """
        pattern = re.compile(
                r'^(?P<path>[^:]+):\s+line\s+(?P<line>\d+),'
                r'(?:.*?),\s(?P<message>.*)'
        )
        for line in output.splitlines():
            match = pattern.match(line)
            if not match:
                continue
            filename = docker.strip_base(match.group('path'))
            line = int(match.group('line'))
            message = match.group('message').strip()
            self.problems.add(filename, line, message)
