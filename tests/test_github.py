from __future__ import absolute_import
import json
from mock import call, Mock
from unittest import TestCase

import lintreview.github as github

from . import load_fixture
import github3
from github3 import GitHub
from github3.session import GitHubSession
from github3.repos import Repository
from github3.repos.hook import Hook


config = {
    'GITHUB_URL': 'https://api.github.com/',
}
session = GitHubSession()


class TestGithub(TestCase):

    def test_get_client(self):
        conf = config.copy()
        conf['GITHUB_OAUTH_TOKEN'] = 'an-oauth-token'
        gh = github.get_client(conf)
        assert isinstance(gh, GitHub)

    def test_get_client__retry_opts(self):
        conf = config.copy()
        conf['GITHUB_OAUTH_TOKEN'] = 'an-oauth-token'
        conf['GITHUB_CLIENT_RETRY_OPTIONS'] = {'backoff_factor': 42}
        gh = github.get_client(conf)

        for proto in ('https://', 'http://'):
            actual = gh.session.get_adapter(proto).max_retries.backoff_factor
            self.assertEqual(actual, 42)

    def test_get_lintrc(self):
        repo = Mock(spec=Repository)
        github.get_lintrc(repo, 'HEAD')
        repo.file_contents.assert_called_with('.lintrc', 'HEAD')

    def test_register_hook(self):
        repo = Mock(spec=Repository,
                    full_name='mark/lint-review')
        repo.hooks.return_value = []

        url = 'http://example.com/review/start'
        github.register_hook(repo, url)

        assert repo.create_hook.called, 'Create not called'
        calls = repo.create_hook.call_args_list
        expected = call(
            name='web',
            active=True,
            config={
                'content_type': 'json',
                'url': url,
            },
            events=['pull_request']
        )
        self.assertEqual(calls[0], expected)

    def test_register_hook__already_exists(self):
        repo = Mock(spec=Repository,
                    full_name='mark/lint-review')
        repo.hooks.return_value = [
            Hook(f, session)
            for f in json.loads(load_fixture('webhook_list.json'))
        ]
        url = 'http://example.com/review/start'

        github.register_hook(repo, url)
        assert repo.create_hook.called is False, 'Create called'

    def test_unregister_hook__success(self):
        repo = Mock(spec=Repository,
                    full_name='mark/lint-review')
        hooks = [
            github3.repos.hook.Hook(f, session)
            for f in json.loads(load_fixture('webhook_list.json'))
        ]
        repo.hooks.return_value = hooks
        url = 'http://example.com/review/start'
        github.unregister_hook(repo, url)
        assert repo.hook().delete.called, 'Delete not called'

    def test_unregister_hook__not_there(self):
        repo = Mock(spec=Repository,
                    full_name='mark/lint-review')
        repo.hooks.return_value = []
        url = 'http://example.com/review/start'

        self.assertRaises(Exception,
                          github.unregister_hook,
                          repo,
                          url)

        repo.hook().delete.asert_called()
