from __future__ import absolute_import
import logging
import os
import lintreview.docker as docker
from lintreview.review import IssueComment
from lintreview.tools import Tool, process_quickfix

log = logging.getLogger(__name__)


class Golangcilint(Tool):
    """
    Run golangci-lint on files
    """

    name = 'golangcilint'

    def check_dependencies(self):
        """
        See if golint image exists
        """
        return docker.image_exists('golint')

    def match_file(self, filename):
        base = os.path.basename(filename)
        name, ext = os.path.splitext(base)
        return ext == '.go'

    def process_files(self, files):
        """
        Run code checks with golangci-lint.
        """
        command = self.create_command(files)
        output = docker.run('golint', command, self.base_path)
        self._process_output(output)

    def _process_output(self, output):
        lines = output.strip().splitlines()
        if not lines:
            return
        if "Can't read config" in lines[0]:
            msg = (u'Golangci-lint failed and output the following:\n'
                   '```\n'
                   '{}\n'
                   '```\n')
            self.problems.add(IssueComment(msg.format(lines[0])))
            return
        warnings = []
        errors = []
        for line in lines:
            if line.startswith('level='):
                warnings.append(line)
            else:
                errors.append(line)

        if len(warnings):
            msg = (u'Golangci-lint emit the following warnings:\n'
                   '```\n'
                   '{}\n'
                   '```\n')
            warnings = '\n'.join(warnings)
            self.problems.add(IssueComment(msg.format(warnings)))
        process_quickfix(self.problems, errors, docker.strip_base)

    def create_command(self, files):
        command = [
            'golangci-lint', 'run',
            '-j', '1',
            '--out-format', 'line-number',
        ]
        if 'config' in self.options:
            command += ['--config', self.options.get('config')]
        command += files
        return command

    def has_fixer(self):
        """golangci-lint has no fixer
        """
        return False
