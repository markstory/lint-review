import logging
import os
from lintreview.tools import Tool
from lintreview.tools import run_command
from lintreview.utils import in_path
from xml.etree import ElementTree

log = logging.getLogger(__name__)


class Csslint(Tool):

    name = 'csslint'

    def check_dependencies(self):
        """
        See if csslint is on the system path.
        """
        return in_path('csslint')

    def match_file(self, filename):
        base = os.path.basename(filename)
        name, ext = os.path.splitext(base)
        return ext == '.css'

    def process_files(self, files):
        """
        Run code checks with csslint.
        Only a single process is made for all files
        to save resources.
        """
        log.debug('Processing %s files with %s', files, self.name)
        command = ['csslint', '--format=checkstyle-xml']

        # TODO add config options
        if self.options.get('ignore'):
            command += ['--ignore=' + self.options.get('ignore')]
        command += files
        output = run_command(
            command,
            ignore_error=True)
        try:
            tree = ElementTree.fromstring(output)
        except:
            log.debug('Csslint output - %s', output)
            log.error("Unable to parse XML from csslint "
                      "Make sure you have a version of csslint installed ")
            raise

        # Parse checkstyle.xml
        # This might be good for refactoring later.
        for f in tree.iter('file'):
            filename = f.get('name')
            for err in f.iter('error'):
                self.problems.add(
                    filename,
                    int(err.get('line')),
                    err.get('message'))
