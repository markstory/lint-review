from __future__ import absolute_import
from lintreview.fixers.error import WorkflowError
import lintreview.git as git
import logging

log = logging.getLogger(__name__)


class CommitStrategy(object):
    """Fixer strategy for updating the pull request branch in place.
    Appends a commit to the branch that created the pull request.
    """

    def __init__(self, context):
        self.path = context['repo_path']
        self.author_name = context['author_name']
        self.author_email = context['author_email']
        self.pull_request = context['pull_request']

    def execute(self, diffs):
        if not self.pull_request.maintainer_can_modify:
            msg = ('Cannot apply automatic fixing, '
                   'as this pull request cannot be '
                   'modified by maintainers.')
            raise WorkflowError(msg)
        git.create_branch(self.path, 'stylefixes')
        git.checkout(self.path, 'stylefixes')
        for diff in diffs:
            git.apply_cached(self.path, diff.as_diff())

        author = u'{} <{}>'.format(self.author_name, self.author_email)
        remote_branch = self.pull_request.head_branch

        git.commit(self.path, author, 'Fixing style errors.')
        git.push(self.path, 'origin', u'stylefixes:{}'.format(remote_branch))
