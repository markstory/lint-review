from __future__ import absolute_import
import logging
import os
import re
from lintreview.config import comma_value
from lintreview.review import IssueComment
from lintreview.tools import Tool, process_checkstyle
import lintreview.docker as docker

log = logging.getLogger(__name__)


class Eslint(Tool):

    name = 'eslint'

    def check_dependencies(self):
        """See if the nodejs image exists
        """
        return docker.image_exists('nodejs')

    def match_file(self, filename):
        """Check if a file should be linted using ESLint.
        """
        base = os.path.basename(filename)
        name, ext = os.path.splitext(base)
        extensions = comma_value(self.options.get('extensions', '.js,.jsx'))
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
        command = self._create_command()

        command += files
        output = docker.run(
            'nodejs',
            command,
            source_dir=self.base_path)
        self._process_output(output, files)

    def process_fixer(self, files):
        """Run Eslint in the fixer mode.
        """
        command = self.create_fixer_command(files)
        docker.run(
            'nodejs',
            command,
            source_dir=self.base_path)

    def create_fixer_command(self, files):
        command = self._create_command()
        command.append('--fix')
        command += files
        return command

    def _create_command(self):
        command = ['eslint', '--format', 'checkstyle']

        # Add config file or default to recommended linters
        if self.options.get('config'):
            command += ['--config',
                        docker.apply_base(self.options['config'])]
        return command

    def _process_output(self, output, files):
        if '<?xml' not in output:
            return self._config_error(output)
        process_checkstyle(self.problems, output, docker.strip_base)

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
