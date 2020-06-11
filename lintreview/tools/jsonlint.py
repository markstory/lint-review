import os
import lintreview.docker as docker
from lintreview.tools import Tool, process_quickfix


class Jsonlint(Tool):

    name = 'jsonlint'

    def check_dependencies(self):
        """
        See if the python2 image exists
        """
        return docker.image_exists('python2')

    def match_file(self, filename):
        base = os.path.basename(filename)
        name, ext = os.path.splitext(base)
        return ext == '.json'

    def process_files(self, files):
        """
        Run code checks with jsonlint.
        Only a single process is made for all files
        to save resources.
        Configuration is not supported at this time
        """
        command = ['jsonlint']
        command += files

        output = docker.run(
            'python2',
            command,
            source_dir=self.base_path)
        if not output:
            return False

        output = output.split("\n")
        process_quickfix(self.problems, output, docker.strip_base)
