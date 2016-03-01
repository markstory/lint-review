import logging

from lintreview.review import IssueComment
from lintreview.tools import Tool
from lintreview.tools import run_command
from lintreview.utils import in_path

log = logging.getLogger(__name__)


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
        cmd = "git log HEAD^..HEAD --show-signature --format=%H | "
        cmd += "grep -q 'Signature made'"

        try:
            run_command(cmd, split=False, shell=True,
                        ignore_error=False, cwd=self.base_path)
            log.debug('Signature found in HEAD commit')
            return False
        except Exception as e:
            log.debug("Exception: %s" % str(e))
            body = 'No gpg signature for tip of the branch.'
            self.problems.add(IssueComment(body))
