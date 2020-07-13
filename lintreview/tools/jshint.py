import os
from cached_property import cached_property

from lintreview.tools import Tool, process_checkstyle, extract_version
import lintreview.docker as docker


class Jshint(Tool):

    name = 'jshint'

    @cached_property
    def version(self):
        output = docker.run('nodejs', ['jshint', '--version'], self.base_path)
        return extract_version(output)

    def check_dependencies(self):
        """
        See if the nodejs docker image exists
        """
        return docker.image_exists('nodejs')

    def match_file(self, filename):
        base = os.path.basename(filename)
        name, ext = os.path.splitext(base)
        return ext == '.js'

    def process_files(self, files):
        """
        Run code checks with jshint.
        Only a single process is made for all files
        to save resources.
        """
        command = self.create_command(files)
        output = docker.run(
            'nodejs',
            command,
            source_dir=self.base_path)
        process_checkstyle(self.problems, output, False)

    def create_command(self, files):
        command = ['jshint', '--checkstyle-reporter']
        # Add config file if its present
        if self.options.get('config'):
            command += ['--config',
                        docker.apply_base(self.options['config'])]
        command += files
        return command
