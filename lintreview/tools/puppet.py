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
        command = ['bundle', 'exec', 'puppet-lint']
        command += ['--log-format',
                    '%{path}:%{line}:%{column}:%{KIND}:%{message}']
        if self.options.get('config'):
            command += ['-c', self.apply_base(self.options['config'])]
        command += files
        output = docker.run('ruby2', command, self.base_path)

        if not output:
            log.debug('No puppet-lint errors found.')
            return False

        output = output.split("\n")
        process_quickfix(self.problems, output, docker.strip_base)
