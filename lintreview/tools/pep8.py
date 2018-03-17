from __future__ import absolute_import
import os
import logging
import lintreview.docker as docker
from lintreview.tools import Tool, process_quickfix, python_image

log = logging.getLogger(__name__)


class Pep8(Tool):

    name = 'pep8'

    AUTOPEP8_OPTIONS = [
        'exclude',
        'max-line-length',
        'select',
        'ignore',
    ]

    def check_dependencies(self):
        """See if the python2 image exists
        """
        return docker.image_exists('python2')

    def match_file(self, filename):
        base = os.path.basename(filename)
        name, ext = os.path.splitext(base)
        return ext == '.py'

    def process_files(self, files):
        """
        Run code checks with pep8.
        Only a single process is made for all files
        to save resources.
        """
        log.debug('Processing %s files with %s', files, self.name)
        pep8_options = ['exclude',
                        'filename',
                        'select',
                        'ignore',
                        'max-line-length']
        command = ['pep8', '-r']
        for option, value in self.options.items():
            if option in pep8_options:
                command += [u'--{}'.format(option), value]
        command += files

        image = python_image(self.options)
        output = docker.run(image, command, source_dir=self.base_path)
        if not output:
            log.debug('No pep8 errors found.')
            return False
        output = output.split("\n")

        process_quickfix(self.problems, output, docker.strip_base)

    def has_fixer(self):
        """
        pep8 has a fixer that can be enabled through configuration.
        """
        return bool(self.options.get('fixer', False))

    def process_fixer(self, files):
        """Run autopep8, as pep8 has no fixer mode.
        """
        command = self.create_fixer_command(files)
        image = python_image(self.options)
        docker.run(image, command, source_dir=self.base_path)

    def create_fixer_command(self, files):
        command = [
            'autopep8',
            '--in-place',
            '--ignore-local-config',
            '--pep8-passes', '5'
        ]
        for option in self.options:
            if option in self.AUTOPEP8_OPTIONS:
                command.extend([
                    '--%s' % option,
                    self.options.get(option)
                ])
        if 'config' in self.options:
            command.extend(['--global-config', self.options.get('config')])
        command += files
        return command
