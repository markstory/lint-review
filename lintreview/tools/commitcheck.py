from lintreview.tools import Tool
from lintreview.review import IssueComment
import logging
import re


log = logging.getLogger(__name__)


class Commitcheck(Tool):

    name = 'commitcheck'

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
        pattern = self.options.get('pattern').strip("'")

        if not pattern:
            return log.warning('Commit pattern is empty, skipping.')
        try:
            pattern = re.compile(pattern)
        except:
            return log.warning('Commit pattern is invalid, skipping.')

        bad = []
        for commit in commits:
            bad.append(self._check_commit(pattern, commit))
        bad = filter(None, bad)

        if not bad:
            return log.debug('No bad commit messages.')

        body = self.options.get('message', 'The following commits had issues.')
        body = body + ' The pattern %s was not found in:\n' % (
            self.options['pattern'], )
        for commit in bad:
            body += "* %s\n" % (commit, )
        self.problems.add(IssueComment(body))

    def _check_commit(self, pattern, commit):
        match = pattern.search(commit.commit.message)
        if not match:
            return commit.sha
