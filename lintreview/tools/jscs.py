from __future__ import absolute_import
import logging
import os
from lintreview.tools import Tool, process_checkstyle
import lintreview.docker as docker

log = logging.getLogger(__name__)


class Jscs(Tool):

    name = 'jscs'

    def check_dependencies(self):
        """
        See if jscs is on the system path.
        """
        return docker.image_exists('nodejs')

    def match_file(self, filename):
        base = os.path.basename(filename)
        name, ext = os.path.splitext(base)
        return ext == '.js'

    def process_files(self, files):
        """
        Run code checks with jscs.
        Only a single process is made for all files
        to save resources.
        """
        log.debug('Processing %s files with %s', files, self.name)
        command = self.create_command(files)
        output = docker.run(
            'nodejs',
            command,
            source_dir=self.base_path)
        process_checkstyle(self.problems, output, None)

    def create_command(self, files):
        command = ['jscs', '--reporter=checkstyle']
        # Add config file if its present
        if self.options.get('config'):
            command += ['--config',
                        docker.apply_base(self.options['config'])]
        else:
            command += ['--preset', self.options.get('preset', 'google')]
        command += files
        return command
