import os
import re
from cached_property import cached_property

import lintreview.docker as docker
from lintreview.tools import Tool, extract_version

# matches: '  1:4  warning  Incorrect list-item indent: add 1 space  list-item-indent  remark-lint'
# matches: '  18:71-19:1  error  Missing new line after list item  list-item-spacing  remark-lint',
warning_pattern = re.compile(r'^ +(?P<line>\d+):(\d+)(-(\d+):(\d+))? (?P<text>.+)$')
filename_pattern = re.compile(r'^[\S]+.*$')


class Remarklint(Tool):

    name = 'remarklint'

    @cached_property
    def version(self):
        output = docker.run('nodejs', ['run-remark', '--version'], self.base_path)
        return extract_version(output)

    def check_dependencies(self):
        """See if the node image exists
        """
        return docker.image_exists('nodejs')

    def match_file(self, filename):
        base = os.path.basename(filename)
        name, ext = os.path.splitext(base)
        return ext in ('.md', '.markdown')

    def process_files(self, files):
        """
        Run code checks with pep8.
        Only a single process is made for all files
        to save resources.
        """
        command = self.create_command()
        command += map(lambda f: docker.apply_base(f), files)

        output = docker.run('nodejs', command, source_dir=self.base_path)
        if not output:
            return False
        output = output.split("\n")
        filename = None
        # The output from remarklint is a unique format that looks like:
        #
        # >>> file.md
        # >>>   1:1-1:8 warning Some warning
        #
        # We inspect each line to determine if it is a file or warning.
        for line in output:
            if filename_pattern.match(line):
                # Remove the base path as remarklint is fed absolute paths.
                filename = docker.strip_base(line)
            else:
                match = warning_pattern.match(line)
                if match:
                    line = match.group('line')
                    text = match.group('text')
                    self.problems.add(filename, line, text)

    def has_fixer(self):
        """
        remarklint has a fixer that can be enabled through configuration.
        """
        return bool(self.options.get('fixer', False))

    def process_fixer(self, files):
        """Run remarklint, in fixer mode.
        """
        command = self.create_fixer_command(files)
        docker.run('nodejs', command, source_dir=self.base_path)

    def create_command(self):
        # Use the wrapper script for remarklint. See docker/run-remark.sh
        # for more information.
        return ['run-remark', '--no-stdout', '--no-color']

    def create_fixer_command(self, files):
        command = self.create_command()
        command += map(lambda f: docker.apply_base(f), files)
        command.append('-o')
        return command
