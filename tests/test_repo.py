import json

from . import load_fixture
from github3.issues.comment import IssueComment as GhIssueComment
from github3.repos.repo import Repository
from github3.pulls import PullRequest
from lintreview.config import load_config
from lintreview.repo import GithubRepository
from lintreview.repo import GithubPullRequest
from mock import Mock, patch, sentinel
from nose.tools import eq_
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

        assert self.repo_model == repo.repository()
        github_mock.get_repository.assert_called_with(
            config,
            'markstory',
            'lint-test')

    @patch('lintreview.repo.github')
    def test_pull_request(self, github_mock):
        self.repo_model.pull_request = Mock(
            return_value=sentinel.pull_request)
        repo = GithubRepository(config, 'markstory', 'lint-test')
        repo.repository = lambda: self.repo_model
        pull = repo.pull_request(1)
        assert(isinstance(pull, GithubPullRequest),
               'Should be wrapped object')


class TestGithubPullRequest(TestCase):

    def setUp(self):
        fixture = load_fixture('pull_request.json')
        self.model = PullRequest(json.loads(fixture)['pull_request'])

    def test_is_private(self):
        pull = GithubPullRequest(self.model)
        assert False == pull.is_private

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
