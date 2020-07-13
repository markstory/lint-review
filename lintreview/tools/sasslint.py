import os
from cached_property import cached_property

from lintreview.tools import Tool, process_checkstyle, extract_version
import lintreview.docker as docker


class Sasslint(Tool):

    name = 'sasslint'

    @cached_property
    def version(self):
        output = docker.run('nodejs', ['sass-lint', '--version'], self.base_path)
        return extract_version(output)

    def check_dependencies(self):
        """
        See if sass-lint is on the system path.
        """
        return docker.image_exists('nodejs')

    def match_file(self, filename):
        base = os.path.basename(filename)
        name, ext = os.path.splitext(base)
        return ext == '.sass' or ext == '.scss'

    def process_files(self, files):
        """
        Run code checks with sass-lint.
        Only a single process is made for all files
        to save resources.
        """
        command = ['sass-lint', '-f', 'checkstyle', '-v', '-q']
        command += files
        if self.options.get('ignore'):
            command += ['--ignore ', self.options.get('ignore')]
        if self.options.get('config'):
            command += ['--config',
                        docker.apply_base(self.options['config'])]
        output = docker.run(
            'nodejs',
            command,
            source_dir=self.base_path)
        # sass-lint is very silly and outputs multiple xml documents.
        # One for each file...
        for line in output.split("\n"):
            process_checkstyle(self.problems, line, docker.strip_base)
