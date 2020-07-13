import os
from cached_property import cached_property

from lintreview.tools import Tool, process_quickfix, extract_version
import lintreview.docker as docker


class Standardjs(Tool):

    name = 'standardjs'

    @cached_property
    def version(self):
        output = docker.run('nodejs', ['standard', '--version'], self.base_path)
        return extract_version(output)

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
        command = ['standard'] + list(files)
        output = docker.run(
            'nodejs',
            command,
            source_dir=self.base_path)

        output = output.split("\n")
        output = [line for line in output if not line.startswith('standard')]
        process_quickfix(self.problems, output, docker.strip_base)
