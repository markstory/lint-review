import logging
import os
import re

import lintreview.docker as docker
from lintreview.review import IssueComment
from lintreview.tools import Tool, process_quickfix

log = logging.getLogger(__name__)


class Golint(Tool):
    """
    Run golint on files. This may need to offer config options
    to map packages -> dirs so we can run golint once per package.
    """

    name = 'golint'

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
        Run code checks with golint.
        Only a single process is made for all files
        to save resources.
        """
        command = self.create_command(files)
        output = docker.run('golint', command, self.base_path)
        output = output.strip().split("\n")
        # Look for multi-package error message, and re-run tools
        if len(output) == 1 and 'is in package' in output[0]:
            log.info('Re-running golint on individual files '
                     'as diff contains files from multiple packages: %s',
                     output[0])
            self.run_individual_files(files, docker.strip_base)
        else:
            output = self.apply_ignore_rules(output)
            process_quickfix(self.problems, output, docker.strip_base)

    def create_command(self, files):
        command = ['golint']
        if 'min_confidence' in self.options:
            command += ['-min_confidence', self.options.get('min_confidence')]
        command += files
        return command

    def run_individual_files(self, files, filename_converter):
        """
        If we get an error from golint about different packages
        we have to re-run golint on each file as figuring out package
        relations is hard.
        """
        for filename in files:
            command = self.create_command([filename])
            output = docker.run('golint', command, self.base_path)
            output = output.split("\n")
            output = self.apply_ignore_rules(output)
            process_quickfix(self.problems, output, filename_converter)

    def has_fixer(self):
        """golint has a fixer that can be enabled through configuration.
        """
        return bool(self.options.get('fixer', False))

    def process_fixer(self, files):
        """Run gofmt as a fixer for go
        """
        command = self.create_fixer_command(files)
        docker.run(
            'golint',
            command,
            source_dir=self.base_path)

    def create_fixer_command(self, files):
        command = ['gofmt', '-w']
        command += docker.replace_basedir(self.base_path, files)
        return command

    def apply_ignore_rules(self, output):
        if 'ignore' not in self.options:
            return output
        log.info('Filtering golint output with %s rules', len(self.options['ignore']))
        rules = []
        for pattern in self.options['ignore']:
            try:
                rules.append(re.compile(pattern))
            except:
                msg = (u'Invalid golint ignore rule `{}` found. '
                       'Ignore rules were skipped.').format(pattern)
                self.problems.add(IssueComment(msg))
                return output

        def matches_rule(line, rules):
            for rule in rules:
                if rule.search(line):
                    return True
            return False

        return [line for line in output if not matches_rule(line, rules)]
