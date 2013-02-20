import lintreview.github as github

from pygithub3 import Github
from nose.tools import eq_


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
    pass


def test_register_hook__already_exists():
    pass


def test_register_hook__failed():
    pass
