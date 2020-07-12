import logging
import os
from cached_property import cached_property

import lintreview.docker as docker
from lintreview.review import IssueComment
from lintreview.tools import (
    Tool,
    extract_version,
    process_quickfix,
    python_image,
)

buildlog = logging.getLogger('buildlog')


class Flake8(Tool):

    name = 'flake8'
    custom_image = None

    # see: http://flake8.readthedocs.org/en/latest/config.html
    PYFLAKE_OPTIONS = (
        'config',
        'ignore',
        'exclude',
        'filename',
        'format',
        'max-complexity',
        'max-line-length',
        'select',
        'snippet',
    )

    AUTOPEP8_OPTIONS = (
        'exclude',
        'max-line-length',
        'select',
        'ignore',
    )

    ALLOWED_PLUGINS = (
        'flake8-isort',
        'flake8-django',
        'flake8-pytest',
        'flake8-bugbear',
        'flake8-tidy-imports',
        'flake8-docstrings',
    )

    @cached_property
    def version(self):
        output = docker.run('python3', ['flake8', '--version'], self.base_path)
        return extract_version(output)

    def check_dependencies(self):
        """
        See if python2 or python3 image exists
        """
        return docker.image_exists('python2') or docker.image_exists('python3')

    def match_file(self, filename):
        base = os.path.basename(filename)
        name, ext = os.path.splitext(base)
        return ext == '.py'

    def process_files(self, files):
        """
        Run code checks with flake8.
        """
        command = self.make_command(files)
        image = self.get_image_name(files)

        output = docker.run(image, command, source_dir=self.base_path)

        self._cleanup()
        output = output.split("\n")
        process_quickfix(self.problems, output, docker.strip_base)

    def make_command(self, files):
        command = ['flake8']
        if 'config' in self.options:
            self.options['config'] = docker.apply_base(
                self.options['config'])

        if self.options.get('isort', None):
            plugins = self.options.get('plugins', [])
            if isinstance(plugins, list):
                plugins.append('flake8-isort')
                self.options['plugins'] = plugins

        for option in self.options:
            if option in self.PYFLAKE_OPTIONS:
                command.extend([
                    '--%s' % option,
                    self.options.get(option)
                ])
        if 'config' in self.options:
            command.extend(['--format', 'default'])
        else:
            command.append('--isolated')
        command += files
        return command

    def has_fixer(self):
        """
        flake8 has a fixer that can be enabled through configuration.
        """
        return bool(self.options.get('fixer', False))

    def process_fixer(self, files):
        """Run autopep8, as flake8 has no fixer mode.
        """
        command = self.create_fixer_command(files)
        image = self.get_image_name(files)

        docker.run(image, command, self.base_path)

    def create_fixer_command(self, files):
        command = [
            'autopep8',
            '--in-place',
            '--ignore-local-config',
            '--pep8-passes', '5'
        ]
        for option in self.options:
            if option in self.AUTOPEP8_OPTIONS:
                command.extend([
                    '--%s' % option,
                    self.options.get(option)
                ])
        if 'config' in self.options:
            command.extend(['--global-config', self.options.get('config')])
        command += files
        return command

    def get_image_name(self, files):
        """Get the image name based on options

        If the `plugin` option is used a custom image will
        be created.
        """
        image = python_image(self.options)
        plugins = self.options.get('plugins', None)
        if not plugins:
            return image
        if not isinstance(plugins, list):
            plugin_type = plugins.__class__.__name__
            error = IssueComment(
                u'The `flake8.plugins` option must be a list got `{}` instead.'.format(
                    plugin_type
                )
            )
            self.problems.add(error)
            return image

        invalid_plugins = [
            p for p in plugins
            if p not in self.ALLOWED_PLUGINS]
        if invalid_plugins:
            error = IssueComment(
                u'The `flake8.plugins` option contained unsupported plugins {}'.format(
                    u', '.join(invalid_plugins)
                )
            )
            self.problems.add(error)
            return image

        container_name = docker.generate_container_name('flake8', files)
        if self.custom_image is None:
            buildlog.info('Installing flake8 plugins')

            docker.run(
                image,
                ['flake8-install', u','.join(plugins)],
                source_dir=self.base_path,
                name=container_name
            )
            docker.commit(container_name)
            docker.rm_container(container_name)
            self.custom_image = container_name
            buildlog.info('Installed flake8 plugins %s', plugins)

        return container_name

    def _cleanup(self):
        """Remove the custom image
        """
        if self.custom_image is None:
            return
        buildlog.info('Removing custom flake8 image')
        docker.rm_image(self.custom_image)
        self.custom_image = None
