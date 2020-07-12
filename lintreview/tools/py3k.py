import os
import logging
import re

from cached_property import cached_property

import lintreview.docker as docker
from lintreview.tools import Tool, process_quickfix, stringify, extract_version

buildlog = logging.getLogger('buildlog')


class Py3k(Tool):
    """
    $ pylint --py3k is a special mode for porting to python 3 which
    disables other pylint checkers.
    see https://github.com/PyCQA/pylint/issues/761
    """

    name = 'py3k'

    @cached_property
    def version(self):
        output = docker.run('python2', ['pylint', '--version'], self.base_path)
        return extract_version(output)

    def check_dependencies(self):
        """
        See if python image is available
        """
        return docker.image_exists('python2')

    def match_file(self, filename):
        base = os.path.basename(filename)
        name, ext = os.path.splitext(base)
        return ext == '.py'

    def process_files(self, files):
        """
        Run code checks with pylint --py3k.
        Only a single process is made for all files
        to save resources.
        """
        command = self.make_command(files)
        output = docker.run('python2', command, self.base_path)
        if not output:
            return False

        output = output.split("\n")
        output = [line for line in output if not line.startswith("*********")]

        process_quickfix(self.problems, output, docker.strip_base)

    def make_command(self, files):
        msg_template = '{path}:{line}:{column}:{msg_id} {msg}'
        command = [
            'pylint',
            '--py3k',
            '--reports=n',
            '--msg-template',
            msg_template,
        ]
        accepted_options = ('ignore')
        if 'ignore' in self.options:
            command.extend(['-d', stringify(self.options['ignore'])])

        # Pylint's ignore-patterns option is unable to ignore
        # paths, so we have to do that ourselves.
        if 'ignore-patterns' in self.options:
            files = self.apply_ignores(self.options['ignore-patterns'], files)

        for option in self.options:
            if option in accepted_options:
                continue
            buildlog.warning('Set non-existent py3k option: %s', option)
        command.extend(files)
        return command

    def apply_ignores(self, patterns, files):
        matchers = []
        for pattern in stringify(patterns).split(','):
            try:
                matcher = re.compile(pattern)
            except Exception:
                continue
            else:
                matchers.append(matcher)

        def has_match(name):
            return any([
                True
                for matcher in matchers
                if matcher.search(name)
            ])

        keepers = []
        for name in files:
            if not has_match(name):
                keepers.append(name)
        return keepers
