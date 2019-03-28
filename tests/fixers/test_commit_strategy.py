from __future__ import absolute_import
from unittest import TestCase
from lintreview.fixers.commit_strategy import CommitStrategy
from lintreview.fixers.error import WorkflowError
from mock import patch, Mock, sentinel
from ..test_git import setup_repo, teardown_repo, clone_path


class TestCommitStrategy(TestCase):

    def setUp(self):
        setup_repo()

    def tearDown(self):
        teardown_repo()

    def test_init_key_requirements(self):
        keys = ('repo_path', 'author_email', 'author_name',
                'pull_request')
        values = ('some/path', 'lintbot', 'bot@example.com',
                  'pull#1')
        for key in keys:
            context = dict(zip(keys, values))
            del context[key]
            self.assertRaises(KeyError,
                              CommitStrategy,
                              context)

    @patch('lintreview.git.commit')
    @patch('lintreview.git.push')
    @patch('lintreview.git.apply_cached')
    def test_execute__push_error(self, mock_apply, mock_push, mock_commit):
        mock_push.side_effect = IOError(
            '! [remote rejected] stylefixes -> add_date_to_obs '
            '(permission denied)\nerror: failed to push some refs to')
        mock_pull = Mock(
            head_branch='patch-1',
            from_private_fork=False,
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
        self.assertRaises(WorkflowError,
                          strategy.execute,
                          [diff])

    @patch('lintreview.git.commit')
    @patch('lintreview.git.push')
    @patch('lintreview.git.apply_cached')
    def test_execute__git_flow(self, mock_apply, mock_push, mock_commit):
        mock_pull = Mock(
            head_branch='patch-1',
            from_private_fork=False,
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
        self.assertIsNone(out)

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
    def test_execute__no_maintainer_modify(self, mock_commit):
        mock_pull = Mock(
            head_branch='patch-1',
            maintainer_can_modify=False,
            from_private_fork=False)
        context = {
            'repo_path': clone_path,
            'author_name': 'lintbot',
            'author_email': 'lint@example.com',
            'pull_request': mock_pull
        }
        strategy = CommitStrategy(context)

        diff = Mock()
        diff.as_diff.return_value = sentinel.diff
        with self.assertRaises(WorkflowError) as err:
            strategy.execute([diff])

        self.assertIn('Cannot apply automatic fixing', str(err.exception))
        self.assertIn('modified by maintainers', str(err.exception))
        self.assertEqual(0, mock_commit.call_count)

    @patch('lintreview.git.commit')
    def test_execute__private_fork(self, mock_commit):
        mock_pull = Mock(
            head_branch='patch-1',
            maintainer_can_modify=True,
            from_private_fork=True)
        context = {
            'repo_path': clone_path,
            'author_name': 'lintbot',
            'author_email': 'lint@example.com',
            'pull_request': mock_pull
        }
        strategy = CommitStrategy(context)

        diff = Mock()
        diff.as_diff.return_value = sentinel.diff
        with self.assertRaises(WorkflowError) as err:
            strategy.execute([diff])

        self.assertIn('Cannot apply automatic fixing', str(err.exception))
        self.assertIn('private fork', str(err.exception))
        self.assertEqual(0, mock_commit.call_count)
