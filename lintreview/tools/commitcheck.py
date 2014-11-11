from lintreview.tools import Tool
from lintreview.review import IssueComment
import logging
import re


log = logging.getLogger(__name__)


class Commitcheck(Tool):

    name = 'commitcheck'
    options = {
        'pattern': '',
        'message': 'The following commits do not match'
    }

    def check_dependencies(self):
        """
        No dependencies.
        """
        return True

    def execute_commits(self, commits):
        """
        Check all the commit messages in the set for the pattern
        defined in the config file.
        """
        if not len(self.options['pattern']):
            return log.warning('Commit pattern is empty, skipping.')
        try:
            pattern = re.compile(self.options['pattern'])
        except:
            return log.warning('Commit pattern is invalid, skipping.')

        bad = []
        for commit in commits:
            bad.append(self._check_commit(pattern, commit))
        bad = filter(lambda x: x is not None, bad)

        if not len(bad):
            return log.debug('No bad commit messages.')

        msg = self.options['message'] + ' %s:\n' % (self.options['pattern'], )
        for commit in bad:
            msg += "* %s\n" % (commit, )
        self.problems.add(IssueComment(msg))

    def _check_commit(self, pattern, commit):
        match = pattern.match(commit.commit['message'])
        if not match:
            return commit.sha
