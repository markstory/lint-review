from __future__ import absolute_import
import os
import re
import logging
import lintreview.docker as docker
from lintreview.tools import Tool
from lintreview.review import IssueComment

log = logging.getLogger(__name__)


class Pytype(Tool):

    name = 'pytype'

    def check_dependencies(self):
        """See if the python3 image exists
        """
        return docker.image_exists('python3')

    def match_file(self, filename):
        base = os.path.basename(filename)
        name, ext = os.path.splitext(base)
        return ext in ('.py', '.pyi')

    def has_fixer(self):
        """pytype has a fixer that can be enabled through configuration.
        """
        return bool(self.options.get('fixer', False))

    def process_files(self, files):
        """
        Run code checks with pytype.
        Only a single process is made for all files
        to save resources.
        """
        log.debug('Processing %s files with %s', files, self.name)
        command = self._apply_options(['pytype'])
        command += files

        output = docker.run(
            'python3',
            command,
            source_dir=self.base_path,
            run_as_current_user=True)
        if not output:
            return

        self.parse_output(output)

    def _apply_options(self, command):
        if 'config' in self.options:
            command.extend(['--config', docker.apply_base(self.options['config'])])
        return command

    def parse_output(self, output):
        """
        Pytype has is own output format that is not machine readable, so we use
        regex and string contains to munge it into something usable. The output looks like

        ```
        Computing dependencies
        Analyzing 1 sources with 0 local dependencies
        ninja: Entering directory `/src/.pytype'
        [1/1] check has_errors
        FAILED: /src/.pytype/pyi/has_errors.pyi
        pytype-single --imports_info /src/.pytype/imports/has_errors.imports ...
        File "../pytype/has_errors.py", line 5, in get_username: message text [attribute-error]
          In Optional[Match[str]]
        File "../pytype/has_errors.py", line 8, in <module>: message text: '1' [bad-slots]
        ```

        We use regex to slice out the file, line and message information.
        """
        message = ''
        lineno = 0
        filename = ''

        message_pattern = re.compile(
            r'File "(?P<file>[^"]+)",\s+line\s+(?P<line>\d+),[^:]+\:\s+(?P<message>.*)'
        )
        lines = output.split('\n')
        if len(lines) and lines[0].startswith('CRITICAL'):
            message = (
                u"Pytype failed with the following error:\n"
                "```\n"
                "{}\n"
                "```\n"
            )
            self.problems.add(IssueComment(message.format("\n".join(lines))))

        for line in output.split("\n"):
            # Some errors have continuations on subsequent lines
            if len(message) and not line.startswith('File'):
                message = message + ' ' + line.strip()
                continue
            if line.startswith('File '):
                # Starting a new message append to the error list.
                if filename and message:
                    self.problems.add(filename, lineno, message)
                    filename = ''
                    lineno = 0
                    message = ''

                matches = message_pattern.match(line)

                lineno = int(matches.group('line'))
                filename = docker.strip_base(matches.group('file'))
                message = matches.group('message')
        if filename and message:
            self.problems.add(filename, lineno, message)

    def process_fixer(self, files):
        """
        Autofixing typing errors requires generating type
        stubs and then applying them individually.
        """
        command = self._apply_options(['pytype'])
        command += files
        out = docker.run(
            'python3',
            command,
            source_dir=self.base_path,
            run_as_current_user=True)

        for f in files:
            basename = os.path.basename(f)
            type_file = os.path.join(
                '.pytype',
                'pyi',
                basename[:-3] + '.pyi')
            command = ['merge-pyi', '-i', f, docker.apply_base(type_file)]
            out = docker.run('python3', command, source_dir=self.base_path)
