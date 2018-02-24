from __future__ import absolute_import
import logging
import os
import lintreview.docker as docker
from lintreview.tools import Tool, process_checkstyle


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
        command = [cmd, '--format=checkstyle-xml']

        if self.options.get('ignore'):
            command += ['--ignore=' + self.options.get('ignore')]
        command += files

        output = docker.run(
            'nodejs',
            command,
            source_dir=self.base_path)
        process_checkstyle(self.problems, output, docker.strip_base)
