from __future__ import absolute_import
import logging
import os
import lintreview.docker as docker
from lintreview.review import IssueComment
from lintreview.tools import Tool, process_checkstyle

log = logging.getLogger(__name__)


class Checkstyle(Tool):

    name = 'checkstyle'

    def check_dependencies(self):
        """
        See if checkstyle image exists
        """
        return docker.image_exists('checkstyle')

    def match_file(self, filename):
        base = os.path.basename(filename)
        name, ext = os.path.splitext(base)
        return ext == '.java'

    def process_files(self, files):
        """
        Run code checks with checkstyle.
        Only a single process is made for all files
        to save resources.
        """
        log.debug('Processing %s files with %s', files, self.name)
        if 'config' not in self.options:
            msg = ("We could not run `checkstyle` you did not set "
                   "the `config` option to a valid checkstyle XML file.")
            return self.problems.add(IssueComment(msg))
        command = self.create_command(files)
        output = docker.run('checkstyle', command, self.base_path)

        # Only one line is generally a config error. Replay the error
        # to the user.
        lines = output.strip().split('\n')
        if not lines[0].startswith('<'):
            msg = ("Running `checkstyle` failed with:\n"
                   "```\n"
                   "%s\n"
                   "```\n"
                   "Ensure your config file exists and is valid XML.")
            return self.problems.add(IssueComment(msg % (lines[0],)))

        # Remove the last line if it is not XML
        # Checkstyle outputs text after the XML if there are errors.
        if not lines[-1].strip().startswith('<'):
            lines = lines[0:-1]
        output = ''.join(lines)

        process_checkstyle(self.problems, output, docker.strip_base)

    def create_command(self, files):
        command = [
            'checkstyle',
            '-f', 'xml',
            '-c', docker.apply_base(self.options['config'])
        ]
        command += files
        return command
