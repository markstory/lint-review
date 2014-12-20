import logging
import os
import re
from lintreview.tools import Tool
from lintreview.tools import run_command
from lintreview.utils import in_path
from lintreview.utils import npm_exists

log = logging.getLogger(__name__)


class UnsafeHandlebars(Tool):

    name = 'unsafe-handlebars'

    def check_dependencies(self):
        """
        See if grep is on the system path.
        """
        return in_path('grep') or npm_exists('grep')

    def match_file(self, filename):
        base = os.path.basename(filename)
        name, ext = os.path.splitext(base)
        # Some .js can hand-compile handlebar templates
        return ext == '.js' or ext == '.hbs'

    def process_files(self, files):
        """
        grep the files for any unsafe variables (using three curly-braces)
        """
        log.debug('Processing %s files with %s', files, self.name)
        command = self.create_command(files)
        output = run_command(
            command,
            split=True,
            ignore_error=True, # no matches returns exit status of 1
            shell=True)
        for line in output:
            re_result = re.search('^(.*?):([0-9]+):\s*(.*?)$', line)
            if re_result is None:
                return

            filename, lineNumber, lineContents = re_result.groups()
            lineNumber = int(lineNumber)
            message = """
:warning: Warning! Potential XSS vulnerability. Are you sure you intended to use 3 curlybraces?

```
%s
```
""" % lineContents
            self.problems.add(filename, lineNumber, message)

    def create_command(self, files):
        cmd = 'grep'
        if npm_exists('grep'):
            cmd = os.path.join(os.getcwd(), 'node_modules', '.bin', 'grep')
        command = [cmd, '-nR', '"{{{~\\?[A-Za-z.]\\+~\\?}}}"']
        command += files
        return command
