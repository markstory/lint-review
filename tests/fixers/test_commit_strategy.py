from __future__ import absolute_import
from lintreview.fixers.commit_strategy import CommitStrategy
from lintreview.fixers.error import WorkflowError
from mock import patch, Mock, sentinel
from nose.tools import assert_in, assert_raises, with_setup, eq_
from ..test_git import setup_repo, teardown_repo, clone_path


def test_init_key_requirements():
    keys = ('repo_path', 'author_email', 'author_name',
            'pull_request')
    values = ('some/path', 'lintbot', 'bot@example.com',
              'pull#1')
    for key in keys:
        context = dict(zip(keys, values))
        del context[key]
        with assert_raises(KeyError):
            CommitStrategy(context)


@with_setup(setup_repo, teardown_repo)
@patch('lintreview.git.commit')
@patch('lintreview.git.push')
@patch('lintreview.git.apply_cached')
def test_execute__git_flow(mock_apply, mock_push, mock_commit):
    mock_pull = Mock(
        head_branch='patch-1',
        maintainer_can_modify=True)
    context = {
        'repo_path': clone_path,
        'author_name': 'lintbot',
        'author_email': 'lint@example.com',
        'pull_request': mock_pull
    }
    strategy = CommitStrategy(context)

    diff = Mock()
    diff.as_diff.return_value = sentinel.diff
    out = strategy.execute([diff])
    eq_(None, out)

    mock_commit.assert_called_with(
        clone_path,
        'lintbot <lint@example.com>',
        'Fixing style errors.')
    mock_push.assert_called_with(
        clone_path,
        'origin',
        'stylefixes:patch-1')
    mock_apply.assert_called_with(
        clone_path,
        sentinel.diff)


@patch('lintreview.git.commit')
def test_execute__no_maintainer_modify(mock_commit):
    mock_pull = Mock(
        head_branch='patch-1',
        maintainer_can_modify=False)
    context = {
        'repo_path': clone_path,
        'author_name': 'lintbot',
        'author_email': 'lint@example.com',
        'pull_request': mock_pull
    }
    strategy = CommitStrategy(context)

    diff = Mock()
    diff.as_diff.return_value = sentinel.diff
    with assert_raises(WorkflowError) as err:
        strategy.execute([diff])

    assert_in('Cannot apply automatic fixing', str(err.exception))
    assert_in('modified by maintainers', str(err.exception))
    eq_(0, mock_commit.call_count)
