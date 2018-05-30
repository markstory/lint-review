from __future__ import absolute_import
import os
import logging
import lintreview.docker as docker
from lintreview.tools import Tool, process_quickfix

log = logging.getLogger(__name__)


class Rubocop(Tool):

    name = 'rubocop'

    def check_dependencies(self):
        """
        See if ruby image exists
        """
        return docker.image_exists('ruby2')

    def match_file(self, filename):
        base = os.path.basename(filename)
        name, ext = os.path.splitext(base)
        return ext == '.rb'

    def process_files(self, files):
        """
        Run code checks with rubocop
        """
        log.debug('Processing %s files with %s', files, self.name)
        command = self._create_command()
        command += files
        output = docker.run('ruby2', command, self.base_path)

        if not output:
            log.debug('No rubocop errors found.')
            return False

        output = output.split("\n")
        process_quickfix(self.problems, output, docker.strip_base)

    def _create_command(self):
        command = ['rubocop', '--format', 'emacs']
        if self.options.get('display_cop_names', False):
            command.append('--display-cop-names')
        else:
            command.append('--no-display-cop-names')
        return command

    def has_fixer(self):
        """
        Rubocop has a fixer that can be enabled through configuration.
        """
        return bool(self.options.get('fixer', False))

    def process_fixer(self, files):
        """Run Rubocop in the fixer mode.
        """
        command = self.create_fixer_command(files)
        docker.run('ruby2', command, self.base_path)

    def create_fixer_command(self, files):
        command = self._create_command()
        command.append('--auto-correct')
        command += files
        return command
