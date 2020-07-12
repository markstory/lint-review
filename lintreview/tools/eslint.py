import logging
import os
import re
from cached_property import cached_property

from lintreview.review import IssueComment
from lintreview.tools import Tool, process_checkstyle, commalist, extract_version
import lintreview.docker as docker

log = logging.getLogger(__name__)
buildlog = logging.getLogger('buildlog')


class Eslint(Tool):

    name = 'eslint'
    custom_image = None

    @cached_property
    def version(self):
        output = docker.run('eslint', ['eslint', '--version'], self.base_path)
        return extract_version(output)

    def check_dependencies(self):
        """See if the nodejs image exists
        """
        return docker.image_exists('eslint')

    def match_file(self, filename):
        """Check if a file should be linted using ESLint.
        """
        base = os.path.basename(filename)
        name, ext = os.path.splitext(base)
        extensions = commalist(self.options.get('extensions', '.js,.jsx'))
        return ext in extensions

    def has_fixer(self):
        """Eslint has a fixer that can be enabled
        through configuration.
        """
        return bool(self.options.get('fixer', False))

    def process_files(self, files):
        """Run code checks with ESLint.
        """
        command = self._create_command()
        command += files

        image_name = self.get_image_name(files)

        output = docker.run(
            image_name,
            command,
            source_dir=self.base_path)
        self._cleanup()
        self._process_output(output, files)

    def process_fixer(self, files):
        """Run Eslint in the fixer mode.
        """
        command = self.create_fixer_command(files)
        image_name = self.get_image_name(files)

        docker.run(
            image_name,
            command,
            source_dir=self.base_path)

    def create_fixer_command(self, files):
        command = self._create_command()
        command.append('--fix')
        command += files
        return command

    def get_image_name(self, files):
        """Run container command to install eslint plugins
        """
        if not self.options.get('install_plugins', False):
            return 'eslint'

        container_name = docker.generate_container_name('eslint', files)
        if self.custom_image is None:
            buildlog.info('Installing additional eslint plugins')
            output = docker.run(
                'eslint',
                ['eslint-install'],
                source_dir=self.base_path,
                name=container_name)

            docker.commit(container_name)
            docker.rm_container(container_name)
            self.custom_image = container_name

            installed = [
                line.strip('add:').strip()
                for line in output.splitlines()
                if line.startswith('add:')
            ]
            buildlog.info('Installed eslint plugins %s', installed)
        return container_name

    def _create_command(self):
        command = [
            'eslint-run',
            'eslint',
            '--format', 'checkstyle'
        ]

        # Add config file or default to recommended linters
        if self.options.get('config'):
            command += ['--config',
                        docker.apply_base(self.options['config'])]
        return command

    def _container_name(self, files):
        """Get the persistent container name for custom plugins.

        This is only used when we have to install custom plugins
        as that requires creating new temporary images.
        """
        if not self.options.get('install_plugins', False):
            return None
        return docker.generate_container_name('eslint', files)

    def _cleanup(self):
        """Remove the named container and temporary image
        """
        if self.custom_image is None:
            return
        buildlog.info('Removing custom eslint image')
        docker.rm_image(self.custom_image)
        self.custom_image = None

    def _process_output(self, output, files):
        # Strip deprecations off as they break XML parsing
        if re.match(r'.*?DeprecationWarning', output):
            log.warning(
                "Received deprecation warning from eslint which should not happen in eslint7."
            )
            output = self._handle_deprecation_warning(output)

        if not output.strip().startswith('<?xml'):
            return self._config_error(output)
        process_checkstyle(self.problems, output, docker.strip_base)

    def _handle_deprecation_warning(self, output):
        lines = output.split('\n')
        warnings = [line for line in lines if 'DeprecationWarning' in line]
        skip_lines = len(warnings)
        msg = u'Your eslint configuration output the following error:\n' \
              '```\n' \
              '{}\n' \
              '```\n'
        warnings = '\n'.join(warnings)
        self.problems.add(IssueComment(msg.format(warnings)))

        return '\n'.join(lines[skip_lines:])

    def _config_error(self, output):
        if 'Cannot read config file' in output:
            if 'no such file' in output and 'config' in self.options:
                msg = (u'Your eslint config file is missing or invalid. '
                       u'Please ensure that `{}` exists and is valid.')
                msg = msg.format(self.options['config'])
                return self.problems.add(IssueComment(msg))

            msg = (u'Your ESLint configuration is not valid, '
                   'and output the following errors:\n'
                   '```\n'
                   '{}\n'
                   '```\n')
            # Grab the first few lines as they contain the
            # JSON/YAML parse error
            error_text = u'\n'.join(output.split('\n')[0:8])
            comment = IssueComment(msg.format(error_text))
            return self.problems.add(comment)

        missing_ruleset = re.search(r'Cannot find module.*', output)
        if missing_ruleset:
            msg = u'Your eslint configuration output the following error:\n' \
                   '```\n' \
                   '{}\n' \
                   '```'
            error = missing_ruleset.group(0)
            return self.problems.add(IssueComment(msg.format(error)))

        missing_plugin = re.search(r'ESLint couldn\'t find the (?:plugin|config).*',
                                   output)
        if missing_plugin:
            line = missing_plugin.group(0)

            msg = u'Your eslint configuration output the following error:\n' \
                  '```\n' \
                  '{}\n' \
                  '```\n' \
                  'The above plugin or config preset is not installed.'
            return self.problems.add(IssueComment(msg.format(line)))
