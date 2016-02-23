import json

from . import load_fixture
from contextlib import contextmanager
from github3.issues.comment import IssueComment as GhIssueComment
from github3.repos.repo import Repository
from github3.pulls import PullRequest
from lintreview.config import load_config
from lintreview.repo import GithubRepository
from lintreview.repo import GithubPullRequest
from mock import Mock, patch, sentinel
from nose.tools import eq_, ok_
from unittest import TestCase

config = load_config()


class TestGithubRepository(TestCase):
    def setUp(self):
        fixture = load_fixture('pull_request.json')
        self.repo_model = Repository(json.loads(fixture))

    @patch('lintreview.repo.github')
    def test_repository(self, github_mock):
        github_mock.get_repository.return_value = self.repo_model
        repo = GithubRepository(config, 'markstory', 'lint-test')

        eq_(self.repo_model,repo.repository())
        github_mock.get_repository.assert_called_with(
            config,
            'markstory',
            'lint-test')

    def test_pull_request(self):
        model = self.repo_model
        model.pull_request = Mock(return_value=sentinel.pull_request)
        repo = GithubRepository(config, 'markstory', 'lint-test')
        repo.repository = lambda: self.repo_model
        pull = repo.pull_request(1)
        ok_(isinstance(pull, GithubPullRequest),
               'Should be wrapped object')

    def test_ensure_label__missing(self):
        model = self.repo_model
        model.label = Mock(return_value=None)
        model.create_label = Mock()

        repo = GithubRepository(config, 'markstory', 'lint-test')
        repo.repository = lambda: self.repo_model
        repo.ensure_label('A label')
        model.create_label.assert_called_with(
            name='A label',
            color='bfe5bf')

    def test_ensure_label__exists(self):
        model = self.repo_model
        model.create_label = Mock()
        model.label = Mock(return_value=True)

        repo = GithubRepository(config, 'markstory', 'lint-test')
        repo.repository = lambda: self.repo_model
        repo.ensure_label('A label')
        eq_(False, model.create_label.called)

    def test_create_status(self):
        model = self.repo_model
        model.create_status = Mock()

        repo = GithubRepository(config, 'markstory', 'lint-test')
        repo.repository = lambda: self.repo_model
        repo.create_status('abc123', 'succeeded', 'all good')
        model.create_status.assert_called_with(
            'abc123',
            'succeeded',
            None,
            'all good',
            'lintreview')


class TestGithubPullRequest(TestCase):

    def setUp(self):
        fixture = load_fixture('pull_request.json')
        self.model = PullRequest(json.loads(fixture)['pull_request'])

    def test_is_private(self):
        pull = GithubPullRequest(self.model)
        assert False == pull.is_private

    def test_number(self):
        pull = GithubPullRequest(self.model)
        assert 1 == pull.number

    def test_head(self):
        pull = GithubPullRequest(self.model)
        expected = '53cb70abadcb3237dcb2aa2b1f24dcf7bcc7d68e'
        assert expected == pull.head

    def test_clone_url(self):
        pull = GithubPullRequest(self.model)
        expected = 'https://github.com/markstory/lint-test.git'
        assert expected == pull.clone_url

    def test_target_branch(self):
        pull = GithubPullRequest(self.model)
        assert 'master' == pull.target_branch

    def test_remove_label__label_exists(self):
        pull = GithubPullRequest(self.model)
        label_name = 'No lint errors'
        with add_ok_label(pull, label_name):
            pull.remove_label(label_name)

            pull.pull.issue().remove_label.assert_called_with(label_name)

    def test_remove_label__label_missing(self):
        pull = GithubPullRequest(self.model)
        label_name = 'No lint errors'
        with add_ok_label(pull, 'Other label'):
            pull.remove_label(label_name)
            assert 0 == pull.pull.issue().remove_label.call_count

    def test_add_label(self):
        mock_issue = Mock()
        self.model.issue = lambda: mock_issue
        pull = GithubPullRequest(self.model)
        pull.add_label('No lint errors')
        mock_issue.add_labels.assert_called_with('No lint errors')

    def test_create_comment(self):
        self.model.review_comments = Mock()
        pull = GithubPullRequest(self.model)

        pull.review_comments(text)
        ok_(self.model.review_comments.called,
               'Method should delegate')

    def test_create_comment(self):
        self.model.create_comment = Mock()
        pull = GithubPullRequest(self.model)

        text = 'No lint errors found'
        pull.create_comment(text)
        self.model.create_comment.assert_called_with(text)

    def test_create_review_comment(self):
        self.model.create_review_comment = Mock()
        pull = GithubPullRequest(self.model)

        comment = {
            'body': 'bad whitespace',
            'commit_id': 'abc123',
            'path': 'some/file.php',
            'position': 12
        }
        pull.create_review_comment(**comment)
        self.model.create_review_comment.assert_called_with(
            comment['body'],
            comment['commit_id'],
            comment['path'],
            comment['position'])

@contextmanager
def add_ok_label(pull_request, *labels, **kw):
    if labels:
        class Label(object):
            def __init__(self, name):
                self.name = name
        mock_issue = Mock()
        mock_issue.labels.return_value = [Label(n) for n in labels]
        pull_request.pull.issue = lambda: mock_issue
    yield
