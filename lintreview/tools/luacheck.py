from __future__ import absolute_import
import logging
import os
import lintreview.docker as docker
from lintreview.review import IssueComment
from lintreview.tools import Tool, process_quickfix

log = logging.getLogger(__name__)


class Luacheck(Tool):

    name = 'luacheck'

    def check_dependencies(self):
        """
        See if luacheck image exists
        """
        return docker.image_exists('luacheck')

    def match_file(self, filename):
        base = os.path.basename(filename)
        name, ext = os.path.splitext(base)
        return ext == '.lua'

    def process_files(self, files):
        """
        Run code checks with luacheck.
        """
        log.debug('Processing %s files with %s', files, self.name)
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
