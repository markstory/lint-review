from __future__ import absolute_import
import os
import logging
import lintreview.docker as docker
from lintreview.tools import Tool, process_quickfix

log = logging.getLogger(__name__)


class Puppet(Tool):

    name = 'puppet-lint'

    def check_dependencies(self):
        """
        See if ruby image exists
        """
        return docker.image_exists('ruby2')

    def match_file(self, filename):
        base = os.path.basename(filename)
        name, ext = os.path.splitext(base)
        return ext == '.pp'

    def process_files(self, files):
        """
        Run code checks with puppet-lint
        """
        log.debug('Processing %s files with %s', files, self.name)
        command = self._create_command()
        command += files
        output = docker.run('ruby2', command, self.base_path)

        if not output:
            log.debug('No puppet-lint errors found.')
            return False

        output = output.split("\n")
        process_quickfix(self.problems, output, docker.strip_base)

    def _create_command(self):
        command = ['puppet-lint']
        command += ['--log-format',
                    '%{path}:%{line}:%{column}:%{KIND}:%{message}']
        if self.options.get('config'):
            command += ['-c', self.apply_base(self.options['config'])]
        return command

    def has_fixer(self):
        """
        puppet-lint has a fixer that can be enabled through configuration.
        """
        return bool(self.options.get('fixer', False))

    def process_fixer(self, files):
        """
        Run puppet-lint in fixer mode.
        """
        command = self.create_fixer_command(files)
        docker.run('ruby2', command, self.base_path)

    def create_fixer_command(self, files):
        command = self._create_command()
        command.append('--fix')

        if self.options.get('fixer_ignore'):
            for check in self.options['fixer_ignore'].split(','):
                command.append('--no-{0}-check'.format(check.strip()))
        command += files
        return command
