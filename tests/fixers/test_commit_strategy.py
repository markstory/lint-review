from __future__ import absolute_import
from lintreview.fixers.commit_strategy import CommitStrategy
from mock import patch, Mock, sentinel
from nose.tools import assert_raises, with_setup, eq_
from ..test_git import setup_repo, teardown_repo, clone_path


def test_init_key_requirements():
    keys = ('repo_path', 'author', 'remote_branch')
    values = ('some/path', 'lintbot', 'awesome')
    for key in keys:
        context = dict(zip(keys, values))
        del context[key]
        with assert_raises(KeyError):
            CommitStrategy(context)


@with_setup(setup_repo, teardown_repo)
@patch('lintreview.git.commit')
@patch('lintreview.git.push')
@patch('lintreview.git.apply_cached')
def test_init_execute__git_flow(mock_apply, mock_push, mock_commit):
    context = {
        'repo_path': clone_path,
        'author': 'lintbot <lint@example.com>',
        'remote_branch': 'things'
    }
    strategy = CommitStrategy(context)

    diff = Mock()
    diff.as_diff.return_value = sentinel.diff
    out = strategy.execute([diff])
    eq_(None, out)

    mock_commit.assert_called_with(
        clone_path,
        context['author'],
        'Fixing style errors.')
    mock_push.assert_called_with(
        clone_path,
        'origin',
        'stylefixes:things')
    mock_apply.assert_called_with(
        clone_path,
        sentinel.diff)
