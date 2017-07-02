import functools
import logging
import os
from lintreview.tools import Tool, run_command, process_checkstyle
from lintreview.utils import in_path

log = logging.getLogger(__name__)


class Swiftlint(Tool):

    name = 'swiftlint'

    def check_dependencies(self):
        """
        See if swiftlint is on the system path.
        """
        return in_path('swiftlint')

    def match_file(self, filename):
        """
        Check if a file should be linted using ESLint.
        """
        base = os.path.basename(filename)
        name, ext = os.path.splitext(base)
        return ext == '.swift'

    def process_files(self, files):
        """
        Run code checks with swiftlit.
        """
        log.debug('Processing %s files with %s', files, self.name)

        command = [
            'swiftlint',
            'lint',
            '--quiet',
            '--reporter', 'checkstyle',
            '--use-script-input-files'
        ]

        # swiftlint uses a set of environment variables
        # to lint multiple files at once.
        env = os.environ.copy()
        for index, name in enumerate(files):
            env['SCRIPT_INPUT_FILE_%s' % (index,)] = name
        env['SCRIPT_INPUT_FILE_COUNT'] = str(len(files))

        output = run_command(
            command,
            env=env,
            cwd=self.base_path,
            ignore_error=True)

        filename_converter = functools.partial(
            self._relativize_filename,
            files)
        process_checkstyle(self.problems, output, filename_converter)
