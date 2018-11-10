from __future__ import absolute_import
import logging
import os
import jprops
import lintreview.docker as docker
from lintreview.review import IssueComment
from lintreview.tools import Tool, process_checkstyle

log = logging.getLogger(__name__)


class Checkstyle(Tool):
    """
    Integrates with checkstyle.

    When checkstyle is run a properties file will be generated, that
    defines the following keys:

    - config_loc
    - samedir
    - project_loc
    - basedir

    All of these keys will resolve to your repository's root directory.
    """

    name = 'checkstyle'

    def check_dependencies(self):
        """
        See if checkstyle image exists
        """
        return docker.image_exists('checkstyle')

    def match_file(self, filename):
        base = os.path.basename(filename)
        name, ext = os.path.splitext(base)
        return ext == '.java'

    def process_files(self, files):
        """
        Run code checks with checkstyle.
        Only a single process is made for all files
        to save resources.
        """
        log.debug('Processing %s files with %s', files, self.name)
        if 'config' not in self.options:
            msg = ("We could not run `checkstyle` you did not set "
                   "the `config` option to a valid checkstyle XML file.")
            return self.problems.add(IssueComment(msg))

        props_path = os.path.join(self.base_path, '_lintreview.properties')
        # Close the file before trying to read.
        # There have been problems with reading properties while
        # the file handle is still open.
        with open(props_path, 'w+') as f:
            self.setup_properties(f)
            properties_filename = os.path.basename(f.name)

        command = self.create_command(properties_filename, files)
        output = docker.run('checkstyle', command, self.base_path)

        # Cleanup the generated properties file.
        os.remove(props_path)

        # Only one line is generally a config error. Replay the error
        # to the user.
        lines = output.strip().split('\n')
        if not lines[0].startswith('<'):
            msg = ("Running `checkstyle` failed with:\n"
                   "```\n"
                   "%s\n"
                   "```\n"
                   "Ensure your config file exists and is valid XML.")
            return self.problems.add(IssueComment(msg % (lines[0],)))

        # Remove the last line if it is not XML
        # Checkstyle outputs text after the XML if there are errors.
        if not lines[-1].strip().startswith('<'):
            lines = lines[0:-1]
        output = ''.join(lines)

        process_checkstyle(self.problems, output, docker.strip_base)

    def setup_properties(self, properties_file):
        config_loc = os.path.dirname(docker.apply_base(self.options['config']))
        project_loc = docker.apply_base('/')

        properties = {
            'config_loc': config_loc,
            'samedir': config_loc,
            'project_loc': project_loc,
            'basedir': project_loc,
        }

        jprops.store_properties(properties_file, properties)

    def create_command(self, properties_filename, files):
        command = [
            'checkstyle',
            '-f', 'xml',
            '-p', docker.apply_base(properties_filename),
            '-c', docker.apply_base(self.options['config'])
        ]
        command += files
        return command
