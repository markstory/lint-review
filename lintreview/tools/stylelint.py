import os
from cached_property import cached_property

from lintreview.review import IssueComment
from lintreview.tools import Tool, process_quickfix, extract_version
import lintreview.docker as docker


class Stylelint(Tool):

    name = 'stylelint'

    @cached_property
    def version(self):
        output = docker.run('nodejs', ['stylelint', '--version'], self.base_path)
        return extract_version(output)

    def check_dependencies(self):
        """
        See if nodejs container exists
        """
        return docker.image_exists('nodejs')

    def match_file(self, filename):
        base = os.path.basename(filename)
        name, ext = os.path.splitext(base)
        return ext in ('.sass', '.scss', '.css', '.less')

    def has_fixer(self):
        """stylelint has a fixer that can be enabled
        through configuration.
        """
        return bool(self.options.get('fixer', False))

    def process_files(self, files):
        """
        Run code checks with stylelint.
        """
        command = self._create_command()
        command += files
        output = docker.run(
            'nodejs',
            command,
            source_dir=self.base_path)
        if ('SyntaxError' in output or
                'ENOENT' in output or
                'JSONError' in output):
            msg = (
                u"Your configuration file resulted in the following error:\n"
                "```\n"
                "{}"
                "```\n"
            )
            return self.problems.add(IssueComment(msg.format(output)))
        process_quickfix(self.problems, output.splitlines(), docker.strip_base)

    def process_fixer(self, files):
        """Run stylelint in the fixer mode.
        """
        command = self.create_fixer_command(files)
        docker.run(
            'nodejs',
            command,
            source_dir=self.base_path)

    def _create_command(self):
        command = [
            'stylelint',
            '--formatter', 'unix',
            '--config-basedir', '/tool',
        ]

        if self.options.get('config'):
            command += [
                '--config',
                docker.apply_base(self.options['config'])
            ]
        return command

    def create_fixer_command(self, files):
        command = self._create_command()
        command.append('--fix')
        command += files
        return command
