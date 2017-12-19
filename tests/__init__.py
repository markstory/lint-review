from __future__ import absolute_import
import os
import json
import lintreview.git as git
from github3.pulls import PullFile
from github3.repos.commit import RepoCommit

test_dir = os.path.dirname(os.path.abspath(__file__))
fixtures_path = os.path.join(test_dir, 'fixtures')


def load_fixture(filename):
    filename = os.path.join(fixtures_path, filename)
    fh = open(filename, 'r')
    return fh.read()


def create_pull_files(data):
    return [PullFile(f) for f in json.loads(data)]


def create_commits(data):
    return [RepoCommit(f) for f in json.loads(data)]


def read_file(path):
    with open(path, 'r') as f:
        return f.read()


def read_and_restore_file(path, contents):
    with open(path, 'r') as f:
        updated = f.read()
    with open(path, 'w') as f:
        f.write(contents)
    return updated


clone_path = os.path.join(test_dir, 'test_clone')
cant_write_to_test = not(os.access(test_dir, os.W_OK))


def setup_repo():
    git.clone_or_update(
        {},
        'git://github.com/markstory/lint-review.git',
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
