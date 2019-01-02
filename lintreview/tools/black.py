from __future__ import absolute_import
import os
import logging
import lintreview.docker as docker
from lintreview.review import IssueComment
from lintreview.tools import Tool

log = logging.getLogger(__name__)


class Black(Tool):

    name = 'black'

    def check_dependencies(self):
        """See if the python3 image exists
        """
        return docker.image_exists('python3')

    def match_file(self, filename):
        base = os.path.basename(filename)
        name, ext = os.path.splitext(base)
        return ext == '.py'

    def process_files(self, files):
        """
        Run code checks with black.
        Only a single process is made for all files to save resources.
        """
        log.debug('Processing %s files with %s', files, self.name)
        command = self.create_command()
        command.append('--check')
        command += files

        output = docker.run('python3', command, source_dir=self.base_path)
        if not output:
            return False
        output = output.split("\n")

        effected_files = [
            '* ' + docker.strip_base(line.replace('would reformat ', ''))
            for line in output
            if line.startswith('would reformat')
        ]
        if len(effected_files):
            msg = (
                'The following files do not match the `black` styleguide:'
                '\n\n'
            )
            msg += "\n".join(effected_files)
            self.problems.add(IssueComment(msg))

    def has_fixer(self):
        """
        black has a fixer that can be enabled through configuration.
        """
        return bool(self.options.get('fixer', False))

    def process_fixer(self, files):
        """Run black, in fixer mode.
        """
        command = self.create_fixer_command(files)
        docker.run('python3', command, source_dir=self.base_path)

    def create_command(self):
        command = ['black']
        if 'py36' in self.options:
            command.append('--py36')
        if 'config' in self.options:
            command.extend(['--config',
                            docker.apply_base(self.options['config'])])
        return command

    def create_fixer_command(self, files):
        command = self.create_command()
        command += files
        return command
