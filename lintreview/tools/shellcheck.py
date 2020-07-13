import os
from cached_property import cached_property

import lintreview.docker as docker
from lintreview.tools import Tool, process_checkstyle, extract_version


class Shellcheck(Tool):

    name = 'shellcheck'

    @cached_property
    def version(self):
        output = docker.run('shellcheck', ['shellcheck', '--version'], self.base_path)
        return extract_version(output)

    def check_dependencies(self):
        """
        See if shellcheck image exists
        """
        return docker.image_exists('shellcheck')

    def match_file(self, filename):
        base = os.path.basename(filename)
        name, ext = os.path.splitext(base)
        if ext in ('.sh', '.bash', '.ksh', '.zsh'):
            return True

        if not os.path.exists(filename) or not os.access(filename, os.X_OK):
            return False

        # Check for a shebang in the first line.
        with open(filename, 'r') as f:
            line = f.readline()
            return line.startswith('#!') and (
                'bash' in line or
                'sh' in line or
                'zsh' in line or
                'ksh' in line
            )

    def process_files(self, files):
        """
        Run code checks with shellcheck.
        """
        command = self.create_command(files)
        output = docker.run('shellcheck', command, self.base_path)
        process_checkstyle(self.problems, output, docker.strip_base)
        list(map(self.escape_backtick, self.problems))

    def escape_backtick(self, problem):
        problem.body = problem.body.replace('`', '\\`')

    def create_command(self, files):
        command = ['shellcheck']
        command += ['--format=checkstyle']
        shell = 'sh'
        if self.options.get('shell'):
            shell = self.options['shell']
        command += ['--shell=' + shell]
        if self.options.get('exclude'):
            command += ['--exclude=' + str(self.options['exclude'])]
        command += files
        return command
