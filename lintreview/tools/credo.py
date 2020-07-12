import os
from cached_property import cached_property

import lintreview.docker as docker
from lintreview.tools import Tool, process_quickfix, extract_version


class Credo(Tool):

    name = 'credo'

    @cached_property
    def version(self):
        output = docker.run('credo', ['mix', 'credo', '--version'], self.base_path)
        return extract_version(output)

    def check_dependencies(self):
        return docker.image_exists('credo')

    def match_file(self, filename):
        base = os.path.basename(filename)
        name, ext = os.path.splitext(base)
        return ext in ('.ex', '.exs')

    def process_files(self, files):
        """
        Run code checks with credo.
        """
        command = self.create_command()
        command += files
        output = docker.run('credo', command, self.base_path)
        if not output:
            return False

        process_quickfix(
            self.problems,
            output.strip().splitlines(),
            docker.strip_base,
            columns=4)

    def create_command(self):
        credo_options = ['checks',
                         'config-name',
                         'ignore-checks']
        credo_flags = ['all',
                       'all-priorities',
                       'strict']
        command = ['mix', 'credo', 'list', '--format', 'flycheck']
        for option, value in self.options.items():
            if option in credo_options:
                command += [u'--{}'.format(option), value]
            elif option in credo_flags:
                if self.parse_ini_bool(value):
                    command += [u'--{}'.format(option)]
        return command

    def parse_ini_bool(self, value):
        if value is None:
            return False
        if isinstance(value, bool):
            return value
        if isinstance(value, int):
            return True if value == 1 else False
        true = ['1', 'yes', 'true', 'on']
        return value.lower() in true
