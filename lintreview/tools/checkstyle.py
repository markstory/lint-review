from __future__ import absolute_import
import logging
import os
import re
import six
from tempfile import NamedTemporaryFile
import lintreview.docker as docker
from lintreview.review import IssueComment
from lintreview.tools import Tool, process_checkstyle

log = logging.getLogger(__name__)


class Checkstyle(Tool):

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

        with NamedTemporaryFile(dir=self.base_path,
                                suffix='.properties') as f:
            self.setup_properties(f)
            properties_filename = os.path.basename(f.name)
            command = self.create_command(properties_filename, files)
            output = docker.run('checkstyle', command, self.base_path)

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

    def escape_for_java(self, value):
        """Escapes the values used in Java properties files. Uses special
        characters specified by
        https://docs.oracle.com/javase/8/docs/api/java/util/Properties.html
        """
        replacements = {
            ord(u"#"): u"\\#",
            ord(u"!"): u"\\!",
            ord(u"="): u"\\=",
            ord(u":"): u"\\:",
            ord(u"\\"): u"\\\\",
            ord(u" "): u"\\u0020",
            ord(u"\t"): u"\\u0009",
            ord(u"\f"): u"\\u000C",
            ord(u"\n"): u"\\n",
            ord(u"\r"): u"\\r",
        }

        if not isinstance(value, six.text_type):
            value = value.decode('utf-8')
        value = value.translate(replacements)

        def escape_unicode(match):
            char = ord(match.group(0))
            if char < 0x10000:
                return b"\\u%04x" % ord(match.group(0))
            else:
                char -= 0x10000
                hi = 0xD800 | ((char >> 10) & 0x3FF)
                lo = 0xDC00 | (char & 0x3FF)
                return b"\\u%04x\\u%04x" % (hi, lo)

        return re.sub(r'[^\x20-\x7e]', escape_unicode, value).encode('utf-8')

    def setup_properties(self, properties_file):
        config_loc = os.path.dirname(docker.apply_base(self.options['config']))
        project_loc = docker.apply_base('/')

        properties = {
            'config_loc': config_loc,
            'samedir': config_loc,
            'project_loc': project_loc,
            'basedir': project_loc
        }

        for key, value in properties.items():
            line = u'{0}={1}\n'.format(
                self.escape_for_java(key), self.escape_for_java(value))
            properties_file.write(line.encode('utf-8'))
        properties_file.flush()

    def create_command(self, properties_filename, files):
        command = [
            'checkstyle',
            '-f', 'xml',
            '-p', docker.apply_base(properties_filename),
            '-c', docker.apply_base(self.options['config'])
        ]
        command += files
        return command
