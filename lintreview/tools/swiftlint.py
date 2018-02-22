from __future__ import absolute_import
import logging
import os
import lintreview.docker as docker
from lintreview.tools import Tool, process_checkstyle

log = logging.getLogger(__name__)


class Swiftlint(Tool):

    name = 'swiftlint'

    def check_dependencies(self):
        """
        See if swiftlint is on the system path.
        """
        return docker.image_exists('swiftlint')

    def match_file(self, filename):
        """
        Check if a file should be linted using ESLint.
        """
        base = os.path.basename(filename)
        name, ext = os.path.splitext(base)
        return ext == '.swift'

    def process_files(self, files):
        """
        Run code checks with swiftlit.
        """
        log.debug('Processing %s files with %s', files, self.name)

        command = [
            'swiftlint',
            'lint',
            '--quiet',
            '--reporter', 'checkstyle',
            '--use-script-input-files'
        ]

        # swiftlint uses a set of environment variables
        # to lint multiple files at once.
        env = {}
        for index, name in enumerate(files):
            env['SCRIPT_INPUT_FILE_%s' % (index,)] = name
        env['SCRIPT_INPUT_FILE_COUNT'] = str(len(files))

        output = docker.run(
            'swiftlint',
            command,
            self.base_path,
            env=env)
        process_checkstyle(self.problems, output, docker.strip_base)
