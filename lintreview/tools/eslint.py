from __future__ import absolute_import
import functools
import logging
import os
import re
from lintreview.review import IssueComment
from lintreview.tools import Tool, run_command, process_checkstyle
from lintreview.utils import in_path, npm_exists

log = logging.getLogger(__name__)


class Eslint(Tool):

    name = 'eslint'

    def check_dependencies(self):
        """
        See if ESLint is on the system path.
        """
        return in_path('eslint') or npm_exists('eslint')

    def match_file(self, filename):
        """
        Check if a file should be linted using ESLint.
        """
        base = os.path.basename(filename)
        name, ext = os.path.splitext(base)
        return ext == '.js' or ext == '.jsx'

    def process_files(self, files):
        """
        Run code checks with ESLint.
        """
        log.debug('Processing %s files with %s', files, self.name)
        cmd = self.name
        if npm_exists('eslint'):
            cmd = os.path.join(os.getcwd(), 'node_modules', '.bin', 'eslint')
        command = [cmd, '--format', 'checkstyle']

        # Add config file or default to recommended linters
        if self.options.get('config'):
            command += ['--config', self.apply_base(self.options['config'])]

        command += files
        output = run_command(
            command,
            ignore_error=True)
        self._process_output(output, files)

    def _process_output(self, output, files):
        if '<?xml' not in output:
            return self._config_error(output)

        filename_converter = functools.partial(
            self._relativize_filename,
            files)
        process_checkstyle(self.problems, output, filename_converter)

    def _config_error(self, output):
        if 'Cannot read config file' in output:
            msg = u'Your eslint config file is missing or invalid. ' \
                   u'Please ensure that `{}` exists and is valid.'
            msg = msg.format(self.options['config'])
            return self.problems.add(IssueComment(msg))

        missing_ruleset = re.search(r'Cannot find module.*', output)
        if missing_ruleset:
            msg = u'Your eslint configuration output the following error:\n' \
                   '```\n' \
                   '{}\n' \
                   '```'
            error = missing_ruleset.group(0)
            return self.problems.add(IssueComment(msg.format(error)))

        missing_plugin = re.search(r'ESLint couldn\'t find the plugin.*',
                                   output)
        if missing_plugin:
            line = missing_plugin.group(0)

            msg = u'Your eslint configuration output the following error:\n' \
                  '```\n' \
                  '{}\n' \
                  '```\n' \
                  'The above plugin is not installed.'
            return self.problems.add(IssueComment(msg.format(line)))
