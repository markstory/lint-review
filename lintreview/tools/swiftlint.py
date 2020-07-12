import os
from cached_property import cached_property

import lintreview.docker as docker
from lintreview.review import IssueComment
from lintreview.tools import Tool, process_checkstyle, extract_version


class Swiftlint(Tool):

    name = 'swiftlint'

    @cached_property
    def version(self):
        output = docker.run('swiftlint', ['swiftlint', 'version'], self.base_path)
        return extract_version(output)

    def check_dependencies(self):
        """
        See if swiftlint is on the system path.
        """
        return docker.image_exists('swiftlint')

    def match_file(self, filename):
        """
        Check if a file should be linted using ESLint.
        """
        base = os.path.basename(filename)
        name, ext = os.path.splitext(base)
        return ext == '.swift'

    def process_files(self, files):
        """
        Run code checks with swiftlit.
        """
        command = [
            'swiftlint',
            'lint',
            '--quiet',
            '--reporter', 'checkstyle',
            '--use-script-input-files'
        ]

        # swiftlint uses a set of environment variables
        # to lint multiple files at once.
        env = {}
        for index, name in enumerate(files):
            env['SCRIPT_INPUT_FILE_%s' % (index,)] = name
        env['SCRIPT_INPUT_FILE_COUNT'] = str(len(files))

        output = docker.run(
            'swiftlint',
            command,
            self.base_path,
            env=env)
        if not output.strip().startswith('<?xml'):
            output = self._process_warnings(output)
        process_checkstyle(self.problems, output, docker.strip_base)

    def _process_warnings(self, output):
        warnings = []
        lines = output.split("\n")
        for i, line in enumerate(lines):
            if line.startswith('<?xml'):
                break
            else:
                warnings.append(line)
        if warnings:
            msg = [
                "Your `swiftlint` configuration generated warnings:",
                "```",
                "\n".join(warnings),
                "```",
            ]
            self.problems.add(IssueComment("\n".join(msg)))
        return "\n".join(lines[i:])
