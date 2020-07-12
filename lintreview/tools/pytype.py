import hashlib
import os
import re
import logging
from cached_property import cached_property

import lintreview.docker as docker
from lintreview.tools import Tool, extract_version
from lintreview.review import IssueComment

buildlog = logging.getLogger('buildlog')


class Pytype(Tool):

    name = 'pytype'

    @cached_property
    def version(self):
        output = docker.run('pytype', ['pytype', '--version'], self.base_path)
        return extract_version(output)

    def check_dependencies(self):
        """See if the pytype image exists
        """
        return docker.image_exists('pytype')

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
        command = self._apply_options(['pytype'])
        command += files

        output = docker.run(
            'pytype',
            command,
            source_dir=self.base_path)
        if not output:
            return

        self.parse_output(output)

    def _apply_options(self, command):
        if 'config' in self.options:
            command.extend(['--config', docker.apply_base(self.options['config'])])
        command.extend(['-o', '/tmp/pytype'])
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

    def _container_name(self, files):
        m = hashlib.md5()
        m.update('-'.join(files).encode('utf8'))
        return 'pytype-' + m.hexdigest()

    def process_fixer(self, files):
        """
        Autofixing typing errors requires generating type
        stubs and then applying them individually.
        """
        command = self._apply_options(['pytype'])
        command += files

        container_name = self._container_name(files)

        # run in a container that sticks around so we can
        # run merge-pyi on the output files.
        docker.run(
            'pytype',
            command,
            source_dir=self.base_path,
            name=container_name)

        buildlog.info('Creating cusotm image for pytype')
        docker.commit(container_name)
        docker.rm_container(container_name)

        update_command = ['merge-pyi-wrapper']
        update_command += files

        # Apply merge-pyi
        try:
            out = docker.run(
                container_name,
                update_command,
                source_dir=self.base_path
            )
        except Exception as e:
            buildlog.warning('Pytype merging failed. error=%s output=%s', e, out)
        finally:
            buildlog.info('Removing custom pytype image')
            docker.rm_image(container_name)
