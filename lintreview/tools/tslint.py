import functools
import logging
import os
import re
from lintreview.review import IssueComment
from lintreview.tools import Tool, run_command, process_checkstyle
from lintreview.utils import in_path, npm_exists

log = logging.getLogger(__name__)


class Tslint(Tool):

    name = 'tslint'

    def check_dependencies(self):
        """
        See if TsLint is on the system path.
        """
        return in_path('tslint') or npm_exists('tslint')

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
        cmd = self.name
        if npm_exists('tslint'):
            cmd = os.path.join(os.getcwd(), 'node_modules', '.bin', 'tslint')
        command = [cmd, '--format', 'checkstyle']

        # Add config file or default to recommended linters
        if self.options.get('config'):
            command += ['-c', self.apply_base(self.options['config'])]

        command += files
        output = run_command(
            command,
            ignore_error=True)
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

        filename_converter = functools.partial(
            self._relativize_filename,
            files)
        process_checkstyle(self.problems, output, filename_converter)
