from __future__ import absolute_import

import logging
import os

import lintreview.docker as docker
from lintreview.tools import Tool, process_quickfix, python_image, stringify

log = logging.getLogger(__name__)


class Pylint(Tool):

    name = 'pylint'

    accepted_options = ('disable', 'enable', 'config')

    @property
    def _base_command(self):
        return [
            'pylint',
            '--persistent=n',
            '--reports=n',
            '--score=n',
            '--msg-template',
            '{path}:{line}:{column}:{msg_id} {msg}'
        ]

    def match_file(self, filename):
        base = os.path.basename(filename)
        name, ext = os.path.splitext(base)
        return ext == '.py'

    def process_files(self, files):
        log.debug('Processing %s files with %s', files, self.name)
        command = self.make_command(files)
        image = python_image(self.options)
        output = docker.run(image, command, source_dir=self.base_path)
        if not output:
            log.debug('No %s errors found.', self.name)
            return False

        output = output.split("\n")
        output = [line for line in output if not line.startswith("*********")]

        process_quickfix(self.problems, output, docker.strip_base)

    def make_command(self, files):
        self.check_options()

        command = self._base_command

        if self.options.get('disable'):
            command.extend(['--disable', stringify(self.options['disable'])])

        if self.options.get('enable'):
            command.extend(['--enable', stringify(self.options['enable'])])

        if self.options.get('config'):
            command.extend(['--rcfile', docker.apply_base(stringify(self.options['config']))])

        command.extend(files)
        return command

    def check_options(self):
        for unaccepted_option in set(self.accepted_options) - set(self.options.keys()):
            log.warning('Set non-existent %s option: %s', self.name, unaccepted_option)
