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
        self.remote_url = context['remote_url']
        self.remote_branch = context['remote_branch']

    def execute(self, diffs):
        git.add_remote(self.path, 'upstream', self.remote_url)
        git.create_branch(self.path, 'stylefixes')
        git.checkout(self.path, 'stylefixes')
        for diff in diffs:
            git.apply_cached(self.path, diff.patch)
        git.commit(self.path, self.author, 'Fixing style errors.')
        git.push(self.path, 'upstream', 'stylefixes:' + self.remote_branch)
