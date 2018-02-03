from __future__ import absolute_import
import functools
import logging
import os
import re
from lintreview.review import IssueComment
from lintreview.tools import Tool, run_command, process_checkstyle
from lintreview.utils import in_path, npm_exists
from lintreview.config import comma_value

log = logging.getLogger(__name__)


class Eslint(Tool):

    name = 'eslint'

    def check_dependencies(self):
        """See if ESLint is on the system path.
        """
        working_dir = self.get_working_dir()
        return in_path('eslint') or npm_exists('eslint', cwd=working_dir)

    def match_file(self, filename):
        """Check if a file should be linted using ESLint.
        """
        base = os.path.basename(filename)
        name, ext = os.path.splitext(base)
        extensions = comma_value(self.options.get('extensions', '.js,.jsx'))
        log.debug('Using extensions %s', extensions)
        return ext in extensions

    def has_fixer(self):
        """Eslint has a fixer that can be enabled
        through configuration.
        """
        return bool(self.options.get('fixer', False))

    def process_files(self, files):
        """Run code checks with ESLint.
        """
        log.debug('Processing %s files with %s', files, self.name)

        if self.options.get('install'):
            output = run_command(
                ['npm', 'install'],
                ignore_error=True,
                cwd=self.get_working_dir())
            log.debug('Install output: %s', output)

        command = self._create_command()

        command += files
        output = run_command(
            command,
            ignore_error=True)

        self._process_output(output, files)

    def process_fixer(self, files):
        """Run Eslint in the fixer mode.
        """
        command = self.create_fixer_command(files)
        output = run_command(
            command,
            ignore_error=True,
            include_errors=False)
        log.debug(output)

    def create_fixer_command(self, files):
        command = self._create_command()
        command.append('--fix')
        command += files
        return command

    def _create_command(self):
        cmd = 'eslint'
        working_dir = self.get_working_dir()
        if npm_exists('eslint', cwd=working_dir):
            cmd = os.path.join(working_dir, 'node_modules', '.bin', 'eslint')
        command = [cmd, '--format', 'checkstyle']

        # Add config file or default to recommended linters
        if self.options.get('config'):
            command += ['--config', self.apply_base(self.options['config'])]
        return command

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
