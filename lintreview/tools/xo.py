from __future__ import absolute_import
import logging
import os
from lintreview.tools import Tool, process_checkstyle
import lintreview.docker as docker

log = logging.getLogger(__name__)


class Xo(Tool):

    name = 'xo'

    def check_dependencies(self):
        """
        See if XO is on the system path.
        """
        return docker.image_exists('nodejs')

    def match_file(self, filename):
        """
        Check if a file should be linted using XO.
        """
        base = os.path.basename(filename)
        name, ext = os.path.splitext(base)
        return ext == '.js' or ext == '.jsx'

    def process_files(self, files):
        """
        Run code checks with XO.
        """
        log.debug('Processing %s files with %s', files, self.name)
        command = ['xo', '--reporter', 'checkstyle']

        command += files
        output = docker.run(
            'nodejs',
            command,
            source_dir=self.base_path)
        process_checkstyle(self.problems, output, docker.strip_base)
