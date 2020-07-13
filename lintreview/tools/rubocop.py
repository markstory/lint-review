import os
from cached_property import cached_property

import lintreview.docker as docker
from lintreview.review import IssueComment
from lintreview.tools import Tool, process_quickfix, extract_version


class Rubocop(Tool):

    name = 'rubocop'

    @cached_property
    def version(self):
        output = docker.run('ruby2', ['rubocop', '--version'], self.base_path)
        return extract_version(output)

    def check_dependencies(self):
        """
        See if ruby image exists
        """
        return docker.image_exists('ruby2')

    def match_file(self, filename):
        base = os.path.basename(filename)
        name, ext = os.path.splitext(base)
        return ext == '.rb'

    def process_files(self, files):
        """
        Run code checks with rubocop
        """
        command = self._create_command()
        command += files
        output = docker.run('ruby2', command, self.base_path)
        if not output:
            return
        output = output.split("\n")

        # rubocop will emit warnings at the beginning of its output.
        if '.rubocop.yml' in output[0]:
            warnings = []
            for i, line in enumerate(output):
                # Stack trace when rubocop fails.
                if line.startswith("/usr/local"):
                    continue
                # Likely a lint error.
                elif line.count(":") >= 2:
                    break
                else:
                    warnings.append(line)
            msg = [
                "Your rubocop configuration output the following error:",
                "```",
                "\n".join(warnings),
                "```",
            ]
            self.problems.add(IssueComment("\n".join(msg)))
            output = output[i:]

        process_quickfix(self.problems, output, docker.strip_base)

    def _create_command(self):
        command = ['rubocop', '--format', 'emacs']
        if self.options.get('display_cop_names', False):
            command.append('--display-cop-names')
        else:
            command.append('--no-display-cop-names')
        return command

    def has_fixer(self):
        """
        Rubocop has a fixer that can be enabled through configuration.
        """
        return bool(self.options.get('fixer', False))

    def process_fixer(self, files):
        """Run Rubocop in the fixer mode.
        """
        command = self.create_fixer_command(files)
        docker.run('ruby2', command, self.base_path)

    def create_fixer_command(self, files):
        command = self._create_command()
        command.append('--auto-correct')
        command += files
        return command
