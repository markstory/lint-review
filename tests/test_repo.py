import json

from . import load_fixture
from contextlib import contextmanager
from github3.repos.repo import Repository
from github3.pulls import PullRequest
from github3.session import GitHubSession
from lintreview.config import load_config
from lintreview.repo import GithubRepository
from lintreview.repo import GithubPullRequest
from mock import Mock, patch, sentinel
from unittest import TestCase

config = load_config()


class TestGithubRepository(TestCase):
    def setUp(self):
        fixture = load_fixture('repository.json')
        self.session = GitHubSession()
        self.repo_model = Repository.from_json(fixture, self.session)

    @patch('lintreview.repo.github')
    def test_repository(self, github_mock):
        github_mock.get_repository.return_value = self.repo_model
        repo = GithubRepository(config, 'markstory', 'lint-test')

        self.assertEqual(self.repo_model, repo.repository())
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
        self.assertIsInstance(pull, GithubPullRequest,
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
        self.assertEqual(False, model.create_label.called)

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

    def test_update_checkrun(self):
        model = self.repo_model
        model._patch = Mock()
        model._json = Mock()

        repo = GithubRepository(config, 'markstory', 'lint-test')
        repo.repository = lambda: model
        review = {
            'conclusion': 'success',
            'output': {
                'title': 'No lint errors found',
                'summary': '',
                'annotations': [],
            }
        }
        repo.update_checkrun(99, review)
        model._patch.assert_called_with(
            'https://api.github.com/repos/markstory/lint-test/check-runs/99',
            data=json.dumps(review),
            headers={'Accept': 'application/vnd.github.antiope-preview+json'})
        assert model._json.called


class TestGithubPullRequest(TestCase):

    def setUp(self):
        fixture = load_fixture('pull_request.json')
        self.session = GitHubSession()
        self.model = PullRequest.from_json(fixture, self.session)

    def test_display_name(self):
        pull = GithubPullRequest(self.model)
        assert 'markstory/lint-test/pull/1' == pull.display_name

    def test_number(self):
        pull = GithubPullRequest(self.model)
        assert 1 == pull.number

    def test_head(self):
        pull = GithubPullRequest(self.model)
        expected = 'a840e46033fab78c30fccb31d4d58dd0a8160d40'
        assert expected == pull.head

    def test_base(self):
        pull = GithubPullRequest(self.model)
        expected = '55a0965a0af4165058b17ebd0951fa483e8043c8'
        assert expected == pull.base

    def test_clone_url(self):
        pull = GithubPullRequest(self.model)
        expected = 'https://github.com/contributor/lint-test.git'
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

    def test_create_review(self):
        self.model._post = Mock()
        self.model._json = Mock()
        pull = GithubPullRequest(self.model)
        review = {
            'commit_id': 'abc123',
            'event': 'COMMENT',
            'body': 'Bad things',
            'comments': [
                {'position': 1, 'body': 'Bad space', 'path': 'some/file.php'}
            ]
        }
        pull.create_review(review)
        self.model._post.assert_called_with(
            'https://api.github.com/repos/markstory/lint-test/pulls/1/reviews',
            data=review)
        assert self.model._json.called

    def test_maintainer_can_modify__same_repo(self):
        pull = GithubPullRequest(self.model)
        self.assertEqual(True, pull.maintainer_can_modify)

        fixture = load_fixture('pull_request.json')
        data = json.loads(fixture)
        data['maintainer_can_modify'] = False

        model = PullRequest(data, self.session)
        pull = GithubPullRequest(model)
        self.assertEqual(True, pull.maintainer_can_modify)

    def test_maintainer_can_modify__forked_repo(self):
        fixture = load_fixture('pull_request.json')
        data = json.loads(fixture)

        # Make repo different
        data['head']['repo']['full_name'] = 'contributor/lint-test'
        pull = GithubPullRequest(PullRequest(data, self.session))
        self.assertEqual(True, pull.maintainer_can_modify, 'reflects flag')

        # Different repo reflects flag data
        data['maintainer_can_modify'] = False
        pull = GithubPullRequest(PullRequest(data, self.session))
        self.assertEqual(False, pull.maintainer_can_modify)

        data['maintainer_can_modify'] = True
        pull = GithubPullRequest(PullRequest(data, self.session))
        self.assertEqual(True, pull.maintainer_can_modify)

    def test_clone_url__private_fork__not_a_fork(self):
        fixture = load_fixture('pull_request.json')
        data = json.loads(fixture)

        pull = GithubPullRequest(PullRequest(data, self.session))
        self.assertEqual(False, pull.from_private_fork)
        self.assertEqual(data['head']['repo']['clone_url'], pull.clone_url)
        self.assertEqual('test', pull.head_branch)

    def test_clone_url__private_fork__forked(self):
        fixture = load_fixture('pull_request.json')
        data = json.loads(fixture)

        data['head']['repo']['full_name'] = 'contributor/lint-test'
        data['head']['repo']['fork'] = True

        pull = GithubPullRequest(PullRequest(data, self.session))
        self.assertEqual(False, pull.from_private_fork)

    def test_clone_url__private_fork(self):
        fixture = load_fixture('pull_request.json')
        data = json.loads(fixture)

        data['head']['repo']['full_name'] = 'contributor/lint-test'
        data['head']['repo']['clone_url'] = 'secret-repo'
        data['head']['repo']['fork'] = True
        data['head']['repo']['private'] = True
        pull = GithubPullRequest(PullRequest(data, self.session))
        self.assertEqual(True, pull.from_private_fork)
        self.assertEqual(data['base']['repo']['clone_url'], pull.clone_url)
        self.assertEqual('refs/pull/1/head', pull.head_branch)


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
