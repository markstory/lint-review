import os
import logging
from cached_property import cached_property

import lintreview.docker as docker

from lintreview.tools import Tool, process_quickfix, extract_version

log = logging.getLogger(__name__)


class Ansible(Tool):

    name = 'ansible'

    @cached_property
    def version(self):
        output = docker.run('python2', ['ansible-lint', '--version'], self.base_path)
        return extract_version(output)

    def check_dependencies(self):
        return docker.image_exists('python2')

    def match_file(self, filename):
        base = os.path.basename(filename)
        name, ext = os.path.splitext(base)
        return ext == '.yml'

    def process_files(self, files):
        """
        Run code checks with ansible-lint.
        Only a single process is made for all files
        to save resources.
        """
        command = ['ansible-lint', '-p']
        if self.options.get('ignore'):
            command += ['-x', self.options.get('ignore')]
        command += files
        output = docker.run('python2', command, self.base_path)
        if not output:
            log.debug('No ansible-lint errors found.')
            return False

        output = output.split("\n")
        output.sort()

        process_quickfix(self.problems, output, docker.strip_base)
