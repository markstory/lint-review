import os
from cached_property import cached_property

import lintreview.docker as docker
from lintreview.review import IssueComment
from lintreview.tools import Tool, process_quickfix, stringify, extract_version


class Mypy(Tool):

    name = 'mypy'

    @cached_property
    def version(self):
        output = docker.run('python3', ['mypy', '--version'], self.base_path)
        return extract_version(output)

    def check_dependencies(self):
        return docker.image_exists('python3')

    def match_file(self, filename):
        base = os.path.basename(filename)
        name, ext = os.path.splitext(base)
        return ext == '.py'

    def process_files(self, files):
        """
        Run code checks with mypy.
        Only a single process is made for all files
        to save resources.
        """
        command = ['mypy', '--no-error-summary', '--show-absolute-path']
        if 'config' in self.options:
            command += ['--config-file', stringify(self.options.get('config'))]
        command += files

        output = docker.run('python3', command, source_dir=self.base_path)
        if not output:
            return False
        output = output.strip().split("\n")
        if len(output) and output[-1].startswith('mypy: error:'):
            msg = (u'Your `mypy` configuration file caused `mypy` to fail with:'
                   '\n'
                   '```\n'
                   '{}\n'
                   '```\n'
                   'Please correct the error in your configuration file.')
            self.problems.add(IssueComment(msg.format(output[-1])))
            return

        process_quickfix(self.problems, output, docker.strip_base)
