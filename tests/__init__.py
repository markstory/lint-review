from __future__ import absolute_import
import os
import json
from github3.pulls import PullFile
from github3.repos.commit import RepoCommit


def load_fixture(filename):
    path = os.path.dirname(os.path.abspath(__file__))
    filename = os.path.join(path, 'fixtures', filename)
    fh = open(filename, 'r')
    return fh.read()


def create_pull_files(data):
    return [PullFile(f) for f in json.loads(data)]


def create_commits(data):
    return [RepoCommit(f) for f in json.loads(data)]
