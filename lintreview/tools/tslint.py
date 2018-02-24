from __future__ import absolute_import
import logging
import os
import re
from lintreview.review import IssueComment
from lintreview.tools import Tool, process_checkstyle
import lintreview.docker as docker

log = logging.getLogger(__name__)


class Tslint(Tool):

    name = 'tslint'

    def check_dependencies(self):
        """
        See if nodejs image exists
        """
        return docker.image_exists('nodejs')

    def match_file(self, filename):
        """
        Check if a file should be linted using TSLint.
        """
        base = os.path.basename(filename)
        name, ext = os.path.splitext(base)
        return ext == '.ts'

    def process_files(self, files):
        """
        Run code checks with TSLint.
        """
        log.debug('Processing %s files with %s', files, self.name)
        command = ['tslint', '--format', 'checkstyle']

        # Add config file or default to recommended linters
        if self.options.get('config'):
            command += ['-c',
                        docker.apply_base(self.options['config'])]

        command += files
        output = docker.run(
            'nodejs',
            command,
            source_dir=self.base_path)
        self._process_output(output, files)

    def _process_output(self, output, files):
        missing_ruleset = 'Could not find implementations'
        if missing_ruleset in output:
            msg = u'Your tslint configuration output the following error:\n' \
                   '```\n' \
                   '{}\n' \
                   '```'
            # When tslint fails the error message is trailed by
            # multiple newlines with some bonus space. Use that to segment
            # out the error
            error = re.split(r'\n\s*\n', output)[0]
            return self.problems.add(IssueComment(msg.format(error.strip())))

        if (output.startswith('No valid rules') or
                not output.startswith('<?xml')):
            msg = u'Your tslint config file is missing or invalid. ' \
                   u'Please ensure that `{}` exists and is valid JSON.'
            config = self.options.get('config', 'tslint.json')
            msg = msg.format(config)
            return self.problems.add(IssueComment(msg))

        process_checkstyle(self.problems, output, docker.strip_base)
