from __future__ import absolute_import
import os
import json
import tempfile
from unittest import skipIf
from mock import patch

import lintreview.git as git
import lintreview.docker as docker
from github3.pulls import PullFile
from github3.repos.commit import ShortCommit
from github3.session import GitHubSession

root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
test_dir = os.path.dirname(os.path.abspath(__file__))
fixtures_path = os.path.join(test_dir, 'fixtures')
session = GitHubSession()

temp_repo_dir = tempfile.mkdtemp()


def load_fixture(filename):
    filename = os.path.join(fixtures_path, filename)
    fh = open(filename, 'r')
    return fh.read()


def create_pull_files(data):
    session = GitHubSession()
    return [PullFile(f, session) for f in json.loads(data)]


def create_commits(data):
    session = GitHubSession()
    return [ShortCommit(f, session) for f in json.loads(data)]


def read_file(path):
    with open(path, 'r') as f:
        return f.read()


def read_and_restore_file(path, contents):
    with open(path, 'r') as f:
        updated = f.read()
    with open(path, 'w') as f:
        f.write(contents)
    return updated


_images = {}


def requires_image(image):
    """Decorator for checking docker image existence.

    Image existence is cached on first check.
    """
    if image not in _images:
        _images[image] = docker.image_exists(image)

    return skipIf(not(_images[image]), u'requires the {} image'.format(image))


clone_path = os.path.join(test_dir, 'test_clone')
cant_write_to_test = not(os.access(test_dir, os.W_OK))


@patch('lintreview.git.checkout')
@patch('lintreview.git.fetch')
def setup_repo(mock_fetch, mock_checkout):
    """Set up a repo, avoiding fetch and checkout."""
    git_dir = os.path.join(temp_repo_dir, 'test_clone')
    if not os.path.exists(git_dir):
        git.clone_or_update(
            {},
            'git://github.com/markstory/lint-review.git',
            git_dir,
            'master')

    git.clone_or_update(
        {},
        git_dir,
        clone_path,
        'master')


def teardown_repo():
    if git.exists(clone_path):
        git.destroy(clone_path)


fixer_ini = """
[tools]
linters = phpcs, eslint

[tool_phpcs]
fixer = true

[fixers]
enable = true
"""
