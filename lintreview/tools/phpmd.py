from __future__ import absolute_import
import logging
import os
from lintreview.review import IssueComment
from lintreview.tools import (
    Tool,
    process_pmd
)
import lintreview.docker as docker

log = logging.getLogger(__name__)


class Phpmd(Tool):

    name = 'phpmd'

    def check_dependencies(self):
        """
        See if the php container exists
        """
        return docker.image_exists('php')

    def match_file(self, filename):
        base = os.path.basename(filename)
        name, ext = os.path.splitext(base)
        return ext == '.php'

    def process_files(self, files):
        """
        Run code checks with phpmd.
        Only a single process is made for all files
        to save resources.
        """
        command = self.create_command(files)
        output = docker.run(
            'php',
            command,
            source_dir=self.base_path)

        if not output.startswith('<'):
            msg = ('Your PHPMD configuration output the following error:\n'
                   '```\n'
                   '{}\n'
                   '```')
            error = '\n'.join(output.split('\n')[0:1])
            return self.problems.add(IssueComment(msg.format(error)))

        process_pmd(self.problems, output, docker.strip_base)

    def create_command(self, files):
        command = ['phpmd']
        command.append(','.join(files))
        command.append('xml')
        command.append(self.options.get('ruleset', 'cleancode,codesize,unusedcode'))
        return command
