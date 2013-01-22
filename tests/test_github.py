import lintreview.github as github
import base64

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
