import logging
import os
import functools
from lintreview.review import IssueComment
from lintreview.tools import Tool, run_command
from lintreview.utils import in_path, go_bin_path

log = logging.getLogger(__name__)


def process_quickfix(problems, output, filename_converter):
    """
    Process vim quickfix style results.

    Each element in `output` should be formatted like::

        <filename>:<line>:<col>:[ ]<message>
    """
    for line in output:
        parts = line.split(':', 3)
        message = parts[-1].strip()
        filename = filename_converter(parts[0])
        problems.add(filename, int(parts[1]), message)


class Golint(Tool):
    """
    Run golint on files. This may need to offer config options
    to map packages -> dirs so we can run golint once per package.
    """

    name = 'golint'

    def check_dependencies(self):
        """
        See if golint is on the system path.
        """
        return in_path('golint') or go_bin_path('golint')

    def match_file(self, filename):
        base = os.path.basename(filename)
        name, ext = os.path.splitext(base)
        return ext == '.go'

    def process_files(self, files):
        """
        Run code checks with golint.
        Only a single process is made for all files
        to save resources.
        """
        command = self.create_command(files)
        output = run_command(
            command,
            ignore_error=True,
            split=True)
        # Look for multi-package error message
        if len(output) == 1 and 'is in package' in output[0]:
            self.add_review_issue(output[0], files)
        else:
            filename_converter = functools.partial(
                self._relativize_filename,
                files)
            process_quickfix(self.problems, output, filename_converter)

    def create_command(self, files):
        command = ['golint']
        if go_bin_path('golint'):
            command = [go_bin_path('golint')]
        if 'min_confidence' in self.options:
            command += ['-min_confidence', self.options.get('min_confidence')]
        command += files
        return command

    def add_review_issue(self, output, files):
        """
        Add an issue comment when the diff contains files
        from multiple packages.

        In the future it might be good to have a map of packages
        to glob patterns to allow multi-package projects to be reviewed
        """
        filename = output.split(' ')[0]
        relative = self._relativize_filename(files, filename)
        message = u"Could not complete review - %s" % (
            output.replace(filename, relative),
        )
        self.problems.add(IssueComment(message.strip()))
