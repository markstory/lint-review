from __future__ import absolute_import
from stat import ST_MODE
from datetime import datetime
import os
import lintreview.git as git
from lintreview.fixers import StrategyError
import logging

log = logging.getLogger(__name__)


class CommitStrategy(object):
    """Fixer strategy for updating the pull request branch in place.
    Appends a commit to the branch that created the pull request.
    """

    def __init__(self, context):
        self.path = context['repo_path']
        self.author = context['author']
        self.pull_request = context['pull_request']
        self.repository = context['repository']

    def execute(self, diffs):
        # Reset working tree.
        git.reset_hard(self.path)

        # Get current commit & tree shas
        head_commit_sha = self.pull_request.head
        head_tree_sha = git.tree_sha(self.path, head_commit_sha)
        treedata = []

        # Apply patches to get new target state.
        # Use local file system state to create
        # required git data.
        for diff in diffs:
            git.apply(self.path, diff.as_diff())

            path = self.path + os.sep + diff.filename
            f = open(path, 'r')

            log.info('Creating blob for %s', diff.filename)
            blob_sha = self.repository.create_blob(f.read(), 'utf-8')
            if not blob_sha:
                raise StrategyError('Could not create blob')

            stat = os.stat(path)
            treedata.append({
                'path': diff.filename,
                'mode': str(oct(stat.st_mode))[1:],
                'type': 'blob',
                'sha': blob_sha
            })

        new_tree = self.repository.create_tree(
            tree=treedata,
            base_tree=head_tree_sha)
        if not new_tree:
            raise StrategyError('Could not create tree')

        # Add a new commit for the tree
        new_commit = self.repository.create_commit(
            tree=new_tree.sha,
            parents=[head_commit_sha],
            author={
                'name': 'lintbot',
                'email': 'lintbot@mark-story.com',
                'date': datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ'),
            },
            message='Fixing style errors.')
        if not new_commit:
            raise StrategyError('Could not create commit')

        # Update the remote branch.
        self.repository.update_branch(
            self.pull_request.head_branch,
            new_commit.sha)
