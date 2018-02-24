from __future__ import absolute_import
import logging
import os

from lintreview.review import IssueComment
from lintreview.tools import Tool
from lintreview.tools import run_command

log = logging.getLogger(__name__)


def in_path(name):
    """
    Check whether or not a command line tool
    exists in the system path.

    @return boolean
    """
    for dirname in os.environ['PATH'].split(os.pathsep):
        if os.path.exists(os.path.join(dirname, name)):
            return True
    return False


class Gpg(Tool):

    name = 'gpg'

    def check_dependencies(self):
        """
        See if gpg is on the PATH
        """
        return in_path('gpg')

    def execute_commits(self, commits):
        """
        Check that HEAD commit has gpg signature
        """
        cmd = [
            'git', 'log', 'HEAD^..HEAD',
            '--show-signature', '--format=%H'
        ]

        output = run_command(cmd, ignore_error=True, cwd=self.base_path)
        if 'Signature made' not in output:
            body = 'No gpg signature for tip of the branch.'
            self.problems.add(IssueComment(body))
