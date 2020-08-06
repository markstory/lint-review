import os
import logging

from collections import namedtuple
from cached_property import cached_property

from lintreview import docker
from lintreview.review import IssueComment
from lintreview.tools import (
    Tool,
    process_checkstyle,
    stringify,
    extract_version
)

buildlog = logging.getLogger('buildlog')

Package = namedtuple('Package', ['package', 'name'])

OPTIONAL_PACKAGES = {
    'CakePHP2': Package('cakephp/cakephp-codesniffer:^2.0', 'CakePHP'),
    'CakePHP3': Package('cakephp/cakephp-codesniffer:^3.0', 'CakePHP'),
    'CakePHP4': Package('cakephp/cakephp-codesniffer:^4.0', 'CakePHP'),
}


class Phpcs(Tool):

    name = 'phpcs'
    custom_image = None

    @cached_property
    def version(self):
        output = docker.run('php', ['phpcs', '--version'], self.base_path)
        return extract_version(output)

    def check_dependencies(self):
        """
        See if the php container exists
        """
        return docker.image_exists('php')

    def match_file(self, filename):
        base = os.path.basename(filename)
        name, ext = os.path.splitext(base)
        return ext == '.php'

    def process_files(self, files):
        """
        Run code checks with phpcs.
        Only a single process is made for all files
        to save resources.
        """
        image = self.get_image_name(files)
        command = self.create_command(files)
        output = docker.run(image, command, source_dir=self.base_path)
        self._cleanup()

        # Check for errors from PHPCS or PHP
        output = output.strip()
        if output.startswith('ERROR') or 'Fatal Error' in output:
            msg = ('Your PHPCS configuration output the following error:\n'
                   '```\n'
                   '{}\n'
                   '```')
            error = '\n'.join(output.split('\n')[0:1])
            return self.problems.add(IssueComment(msg.format(error)))
        process_checkstyle(self.problems, output, docker.strip_base)

    def apply_base(self, path):
        """
        PHPCS supports either standard names, or paths
        to standard files. Assume no os.sep implies a built-in standard name
        """
        if os.sep not in path:
            return path
        return docker.apply_base(path)

    def create_command(self, files):
        command = ['phpcs-run', 'phpcs']
        command += ['-q', '--report=checkstyle']
        command = self._apply_options(command)
        command += docker.replace_basedir(self.base_path, files)
        return command

    def _apply_options(self, command):
        standard = 'PSR2'
        if self.options.get('standard'):
            standard = self.options['standard']
            if standard in OPTIONAL_PACKAGES:
                standard = OPTIONAL_PACKAGES[standard].name
            standard = self.apply_base(standard)
        command.append('--standard=' + stringify(standard))

        if self.options.get('ignore'):
            ignore = self.options['ignore']
            command.append('--ignore=' + stringify(ignore))
        if self.options.get('exclude'):
            exclude = self.options['exclude']
            command.append('--exclude=' + stringify(exclude))
        extension = 'php'
        if self.options.get('extensions'):
            extension = self.options['extensions']
        command.append('--extensions=' + stringify(extension))
        if self.options.get('tab_width'):
            command += ['--tab-width=' + stringify(self.options['tab_width'])]
        return command

    def has_fixer(self):
        """PHPCS has a fixer that can be enabled through configuration.
        """
        return bool(self.options.get('fixer', False))

    def process_fixer(self, files):
        """Run PHPCS in the fixer mode.
        """
        image = self.get_image_name(files)
        command = self.create_fixer_command(files)
        docker.run(
            image,
            command,
            source_dir=self.base_path)

    def create_fixer_command(self, files):
        command = ['phpcs-run', 'phpcbf']
        command = self._apply_options(command)
        command += docker.replace_basedir(self.base_path, files)
        return command

    def get_image_name(self, files):
        """Get the image name based on options

        If the `standard` option that is an optional package
        the a custom image will be created.
        """
        image = 'php'

        standard = self.options.get('standard', None)
        if not standard or standard not in OPTIONAL_PACKAGES:
            return image

        if not isinstance(standard, str):
            error = IssueComment(
                u'The `phpcs.standard` option must be a string got `{}` instead.'.format(
                    standard.__class__.__name__
                )
            )
            self.problems.add(error)
            return image

        container_name = docker.generate_container_name('phpcs-', files)
        if self.custom_image is None:
            buildlog.info('Installing phpcs package')

            docker.run(
                image,
                ['phpcs-install', OPTIONAL_PACKAGES[standard].package],
                source_dir=self.base_path,
                name=container_name
            )
            docker.commit(container_name)
            docker.rm_container(container_name)
            self.custom_image = container_name
            buildlog.info('Installed phpcs package %s', standard)

        return container_name

    def _cleanup(self):
        """Remove the custom image
        """
        if self.custom_image is None:
            return
        buildlog.info('Removing custom phpcs image')
        docker.rm_image(self.custom_image)
        self.custom_image = None
