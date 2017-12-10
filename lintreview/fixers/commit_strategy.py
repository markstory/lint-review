from __future__ import absolute_import
import lintreview.git as git
import logging

log = logging.getLogger(__name__)


class CommitStrategy(object):
    """Fixer strategy for updating the pull request branch in place.
    Appends a commit to the branch that created the pull request.
    """

    def __init__(self, context):
        self.path = context['repo_path']
        self.author = context['author']
        self.remote_branch = context['remote_branch']

    def execute(self, diffs):
        git.create_branch(self.path, 'stylefixes')
        git.checkout(self.path, 'stylefixes')
        for diff in diffs:
            git.apply_cached(self.path, diff.as_diff())
        git.commit(self.path, self.author, 'Fixing style errors.')
        git.push(self.path, 'origin', 'stylefixes:' + self.remote_branch)
        # TODO raise an error that is converted into
        # a review error when pushing fails due to access/auth issues.
