from __future__ import absolute_import
import logging
import os
import functools
import collections
from lintreview.review import IssueComment
from lintreview.tools import Tool, process_checkstyle, run_command
from lintreview.utils import composer_exists, in_path
import six

log = logging.getLogger(__name__)


def stringify(value):
    """
    PHPCS uses a , separated strings in many places
    because of how it handles options we have to do bad things
    with string concatenation.
    """
    if isinstance(value, six.string_types):
        return value
    if isinstance(value, collections.Iterable):
        return ','.join(value)
    return str(value)


class Phpcs(Tool):

    name = 'phpcs'

    def check_dependencies(self):
        """
        See if PHPCS is on the system path.
        """
        return in_path('phpcs') or composer_exists('phpcs')

    def match_file(self, filename):
        base = os.path.basename(filename)
        name, ext = os.path.splitext(base)
        return ext == '.php'

    def process_files(self, files):
        """
        Run code checks with phpcs.
        Only a single process is made for all files
        to save resources.
        """
        log.debug('Processing %s files with %s', files, self.name)
        command = self.create_command(files)
        output = run_command(
            command,
            ignore_error=True,
            include_errors=False)
        filename_converter = functools.partial(
            self._relativize_filename,
            files)

        # Check for errors from PHPCS
        if output.startswith('ERROR'):
            msg = ('Your PHPCS configuration output the following error:\n'
                   '```\n'
                   '{}\n'
                   '```')
            error = '\n'.join(output.split('\n')[0:1])
            return self.problems.add(IssueComment(msg.format(error)))
        process_checkstyle(self.problems, output, filename_converter)

    def apply_base(self, path):
        """
        PHPCS supports either standard names, or paths
        to standard files. Assume no os.sep implies a built-in standard name
        """
        if os.sep not in path:
            return path
        return super(Phpcs, self).apply_base(path)

    def create_command(self, files):
        command = ['phpcs']
        if composer_exists('phpcs'):
            command = ['vendor/bin/phpcs']
        command += ['--report=checkstyle']
        command = self._apply_options(command)
        command += files
        return command

    def _apply_options(self, command):
        standard = 'PSR2'
        if self.options.get('standard'):
            standard = self.apply_base(self.options['standard'])
        command.append('--standard=' + stringify(standard))

        if self.options.get('ignore'):
            ignore = self.options['ignore']
            command.append('--ignore=' + stringify(ignore))
        if self.options.get('exclude'):
            exclude = self.options['exclude']
            command.append('--exclude=' + stringify(exclude))
        extension = 'php'
        if self.options.get('extensions'):
            extension = self.options['extensions']
        command.append('--extensions=' + stringify(extension))
        if self.options.get('tab_width'):
            command += ['--tab-width=' + stringify(self.options['tab_width'])]
        return command

    def has_fixer(self):
        """
        PHPCS has a fixer that can be enabled through configuration.
        """
        return bool(self.options.get('fixer', False))

    def execute_fixer(self, files):
        """
        Run PHPCS in the fixer mode.
        """
        log.debug('Fixing %s files with %s', files, self.name)
        command = self.create_fixer_command(files)
        output = run_command(
            command,
            ignore_error=True,
            include_errors=False)
        log.error(output)

    def create_fixer_command(self, files):
        command = ['phpcbf']
        if composer_exists('phpcbf'):
            command = ['vendor/bin/phpcbf']
        command = self._apply_options(command)
        command += files
        return command
