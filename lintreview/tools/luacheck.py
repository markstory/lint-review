import os
from cached_property import cached_property

import lintreview.docker as docker
from lintreview.review import IssueComment
from lintreview.tools import Tool, process_quickfix, extract_version


class Luacheck(Tool):

    name = 'luacheck'

    @cached_property
    def version(self):
        output = docker.run('luacheck', ['luacheck', '--version'], self.base_path)
        return extract_version(output)

    def check_dependencies(self):
        return docker.image_exists('luacheck')

    def match_file(self, filename):
        base = os.path.basename(filename)
        name, ext = os.path.splitext(base)
        return ext == '.lua'

    def process_files(self, files):
        """
        Run code checks with luacheck.
        """
        command = self.create_command(files)
        output = docker.run('luacheck', command, self.base_path)
        output = output.split("\n")
        if len(output) and 'Critical' in output[0]:
            msg = (u"luacheck failed with the following error:\n"
                   u"```\n"
                   u"{}\n"
                   u"```\n")
            self.problems.add(IssueComment(msg.format(output[0])))
            return
        process_quickfix(self.problems, output, docker.strip_base)

    def create_command(self, files):
        command = ['luacheck']
        command += ['--formatter=plain']
        command += ['--codes']
        if self.options.get('config'):
            command += ['--config', docker.apply_base(self.options['config'])]
        command += files
        return command
