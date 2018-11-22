from __future__ import absolute_import
import hashlib
import logging
import os
import lintreview.docker as docker
from lintreview.review import IssueComment
from lintreview.tools import Tool, process_quickfix

log = logging.getLogger(__name__)


class ConfigError(Exception):
    pass


VALID_INSTALLERS = ('mod', 'dep', 'govendor')


class Golangcilint(Tool):
    """
    Run golangci-lint on files
    """

    name = 'golangcilint'

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
        Run code checks with golangci-lint.
        """
        try:
            container_name = self._container_name(files)
            self.install_dependencies(container_name)
        except ConfigError as e:
            self.problems.add(IssueComment(str(e)))
            return

        command = self.create_command(files)
        output = docker.run(container_name, command, self.base_path)
        self._cleanup(container_name)
        self._process_output(output)

    def _container_name(self, files):
        """Get the persistent container name
        This is used to store the installed application
        dependencies
        """
        m = hashlib.md5()
        m.update('-'.join(files).encode('utf8'))
        return 'golint-' + m.hexdigest()

    def _cleanup(self, container_name):
        """Remove the named container and temporary image
        """
        # Don't remove the base golint image.
        if container_name == 'golint':
            return
        log.info('Removing temporary image %s', container_name)
        docker.rm_image(container_name)

    def install_dependencies(self, container_name):
        """Run container command to install dependencies
        """
        log.info('Installing golang dependencies into %s',
                 container_name)
        installer = self.options.get('installer', 'mod')
        if installer not in VALID_INSTALLERS:
            msg = (u"The installer `{}` is not supported. "
                   u"Use one of {}.")
            raise ConfigError(
                msg.format(installer, ', '.join(VALID_INSTALLERS)))
        docker.run(
            'golint',
            ['golang-install', installer],
            source_dir=self.base_path,
            name=container_name)

        docker.commit(container_name)
        docker.rm_container(container_name)

    def _process_output(self, output):
        lines = output.strip().splitlines()
        if not lines:
            return
        if "Can't read config" in lines[0]:
            msg = (u'Golangci-lint failed and output the following:\n'
                   '```\n'
                   '{}\n'
                   '```\n')
            self.problems.add(IssueComment(msg.format(lines[0])))
            return
        warnings = []
        errors = []
        for line in lines:
            if line.startswith('level='):
                warnings.append(line)
            else:
                errors.append(line)

        if len(warnings):
            msg = (u'Golangci-lint emit the following warnings:\n'
                   '```\n'
                   '{}\n'
                   '```\n')
            warnings = '\n'.join(warnings)
            self.problems.add(IssueComment(msg.format(warnings)))
        process_quickfix(self.problems, errors, docker.strip_base)

    def create_command(self, files):
        command = [
            'golangci-lint', 'run',
            '-j', '1',
            '--out-format', 'line-number',
        ]
        if 'config' in self.options:
            command += ['--config', self.options.get('config')]
        command.append('./...')
        return command

    def has_fixer(self):
        """golangci-lint has no fixer
        """
        return False
