from __future__ import absolute_import
import os
import logging
import lintreview.docker as docker
from lintreview.review import IssueComment
from lintreview.tools import Tool, process_quickfix

log = logging.getLogger(__name__)


class Yamllint(Tool):

    name = 'yamllint'

    def check_dependencies(self):
        """
        See if python2 image is installed
        """
        return docker.image_exists('python2')

    def match_file(self, filename):
        base = os.path.basename(filename)
        name, ext = os.path.splitext(base)
        return ext in ['.yml', '.yaml']

    def process_files(self, files):
        """
        Run code checks with yamllint.
        Only a single process is made for all files
        to save resources.
        Configuration is not supported at this time
        """
        log.debug('Processing %s files with %s', files, self.name)

        command = ['yamllint', '--format=parsable']
        # Add config file if its present
        if self.options.get('config'):
            command += [
                '-c',
                docker.apply_base(self.options['config'])
            ]
        command += files

        output = docker.run('python2', command, self.base_path)
        if not output:
            log.debug('No yamllint errors found.')
            return False

        if 'No such file' in output and 'Traceback' in output:
            error = output.strip().split("\n")[-1]
            msg = (u'`yamllint` failed with the following error:\n'
                   '```\n'
                   '{}\n'
                   '```\n')
            return self.problems.add(IssueComment(msg.format(error)))

        output = output.split("\n")
        process_quickfix(self.problems, output, docker.strip_base)
