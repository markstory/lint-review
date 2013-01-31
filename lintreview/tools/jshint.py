import os
from lintreview.tools import Tool
from lintreview.tools import run_command
from lintreview.utils import in_path


class Jshint(Tool):

    name = 'jshint'

    def check_dependencies(self):
        """
        See if jshint is on the system path.
        """
        return in_path('jshint')

    def match_file(self, filename):
        base = os.path.basename(filename)
        name, ext = os.path.splitext(base)
        return ext == '.js'

    def process_files(self, files):
        """
        Run code checks with jshint.
        Only a single process is made for all files
        to save resources.
        """
        command = ['jshint']
        command += files
        output = run_command(command, split=True, ignore_error=True)
