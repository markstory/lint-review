import lintreview.github as github

from . import load_fixture
from mock import call, Mock
from nose.tools import eq_
import github3
from github3 import GitHub
import json


config = {
    'GITHUB_URL': 'https://api.github.com/',
    'GITHUB_USER': 'octocat',
    'GITHUB_PASSWORD': 'secrets'
}


def test_get_client():
    gh = github.get_client(config)
    assert isinstance(gh, GitHub)


def test_get_lintrc():
    repo = Mock(spec=github3.repos.repo.Repository)
    github.get_lintrc(repo, 'HEAD')
    repo.file_contents.assert_called_with('.lintrc', 'HEAD')


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
    repo.hooks.return_value = map(
        lambda f: github3.repos.hook.Hook(f),
        json.loads(load_fixture('webhook_list.json')))
    url = 'http://example.com/review/start'

    github.register_hook(repo, url)
    assert repo.create_hook.called is False, 'Create called'


def test_unregister_hook__success():
    repo = Mock(spec=github3.repos.repo.Repository,
                full_name='mark/lint-review')
    hooks = map(lambda f: github3.repos.hook.Hook(f),
                json.loads(load_fixture('webhook_list.json')))
    repo.hooks.return_value = hooks
    url = 'http://example.com/review/start'
    github.unregister_hook(repo, url)
    assert repo.hook().delete.called, 'Delete not called'


def test_unregister_hook__not_there():
    repo = Mock(spec=github3.repos.repo.Repository,
                full_name='mark/lint-review')
    repo.hooks.return_value = []
    url = 'http://example.com/review/start'

    try:
        github.unregister_hook(repo, url)
        assert False, 'No exception'
    except:
        assert True, 'Exception raised'
    assert repo.hook().delete.called is False, 'Delete called'
