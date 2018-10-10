from __future__ import absolute_import
import logging
import os
from lintreview.tools import Tool, process_quickfix
import lintreview.docker as docker

log = logging.getLogger(__name__)


class Standardjs(Tool):

    name = 'standardjs'

    def check_dependencies(self):
        """
        See if standard is on the system path.
        """
        return docker.image_exists('nodejs')

    def match_file(self, filename):
        """
        Check if a file should be linted using standard.
        """
        base = os.path.basename(filename)
        name, ext = os.path.splitext(base)
        return ext == '.js'

    def process_files(self, files):
        """
        Run code checks with standard.
        """
        log.debug('Processing %s files with %s', files, self.name)
        command = ['standard'] + list(files)
        output = docker.run(
            'nodejs',
            command,
            source_dir=self.base_path)

        output = output.split("\n")
        output = [line for line in output if not line.startswith('standard')]
        process_quickfix(self.problems, output, docker.strip_base)
