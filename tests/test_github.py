import lintreview.github as github

from . import load_fixture
from mock import call, patch, Mock
from nose.tools import eq_
import github3
import json


config = {
    'GITHUB_URL': 'https://api.github.com/',
    'GITHUB_USER': 'octocat',
    'GITHUB_PASSWORD': ''
}


def test_get_client():
    gh = github.get_client(config, 'markstory', 'lint-review')
    assert isinstance(gh, Github)


def test_get_lintrc():
    gh = github.get_client(config, 'markstory', 'lint-review')
    lintrc = github.get_lintrc(gh)
    assert lintrc is not None, 'Should get something'
    assert isinstance(lintrc, str)


def test_register_hook():
    repo = Mock(spec=github3.repos.repo.Repository,
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
    eq_(calls[0], expected)


def test_register_hook__already_exists():
    repo = Mock(spec=github3.repos.repo.Repository,
                full_name='mark/lint-review')
    repo.hooks.return_value = map(lambda f: github3.repos.hook.Hook(f),
                                 json.loads(load_fixture('webhook_list.json')))
    url = 'http://example.com/review/start'

    github.register_hook(repo, url)
    assert repo.create_hook.called is False, 'Create called'


@patch('pygithub3.core.client.Client.get')
def test_unregister_hook__success(http):
    response = Response()
    response._content = load_fixture('webhook_list.json')
    http.return_value = response

    gh = Github()
    gh.repos.hooks.delete = Mock()
    url = 'http://example.com/review/start'

    github.unregister_hook(gh, url, 'mark', 'lint-test')

    assert gh.repos.hooks.delete.called, 'Delete not called'


@patch('pygithub3.core.client.Client.get')
def test_unregister_hook__not_there(http):
    response = Response()
    response._content = "[]"
    http.return_value = response

    gh = Github()
    gh.repos.hooks.delete = Mock()
    url = 'http://example.com/review/start'

    try:
        github.unregister_hook(gh, url, 'mark', 'lint-test')
        assert False, 'No exception'
    except:
        assert True, 'Exception raised'
    assert gh.repos.hooks.delete.called is False, 'Delete called'
