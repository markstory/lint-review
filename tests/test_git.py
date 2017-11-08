from __future__ import absolute_import
import lintreview.git as git
import os
from .test_github import config
from nose.tools import eq_, raises, assert_in
from unittest import skipIf

settings = {
    'WORKSPACE': './tests'
}
clone_path = settings['WORKSPACE'] + '/test_clone'
cant_write_to_test = not(os.access(os.path.abspath('./tests'), os.W_OK))


def teardown():
    if git.exists(clone_path):
        git.destroy(clone_path)


def test_get_repo_path():
    user = 'markstory'
    repo = 'asset_compress'
    num = '4'
    res = git.get_repo_path(user, repo, num, settings)
    expected = os.sep.join(
        (settings['WORKSPACE'], user, repo, num))
    expected = os.path.realpath(expected)
    eq_(res, expected)


def test_get_repo_path__int():
    user = 'markstory'
    repo = 'asset_compress'
    num = 4
    res = git.get_repo_path(user, repo, num, settings)
    expected = os.sep.join(
        (settings['WORKSPACE'], user, repo, str(num)))
    expected = os.path.realpath(expected)
    eq_(res, expected)


def test_get_repo_path__absoulte_dir():
    user = 'markstory'
    repo = 'asset_compress'
    num = 4
    settings['WORKSPACE'] = os.path.realpath(settings['WORKSPACE'])
    res = git.get_repo_path(user, repo, num, settings)
    expected = os.sep.join(
        (settings['WORKSPACE'], user, repo, str(num)))
    expected = os.path.realpath(expected)
    eq_(res, expected)


def test_exists__no_path():
    assert not git.exists(settings['WORKSPACE'] + '/herp/derp')


def test_exists__no_git():
    assert not git.exists(settings['WORKSPACE'])


@raises(IOError)
def test_repo_clone_no_repo():
    git.clone(
        'git://github.com/markstory/it will never work.git',
        clone_path)


@skipIf(cant_write_to_test, 'Cannot write to ./tests skipping')
def test_repo_operations():
    res = git.clone(
        'git://github.com/markstory/lint-review.git',
        clone_path)
    assert res, 'Cloned successfully.'
    assert git.exists(clone_path), 'Cloned dir should be there.'
    git.destroy(clone_path)
    assert not(git.exists(clone_path)), 'Cloned dir should be gone.'


@skipIf(cant_write_to_test, 'Cannot write to ./tests skipping')
def test_clone_or_update():
    git.clone_or_update(
        config,
        'git://github.com/markstory/lint-review.git',
        clone_path,
        'e4f880c77e6b2c81c81cad5d45dd4e1c39b919a0')
    assert git.exists(clone_path)


@skipIf(cant_write_to_test, 'Cannot write to ./tests skipping')
def test_diff():
    git.clone_or_update(
        config,
        'git://github.com/markstory/lint-review.git',
        clone_path,
        'master')
    with open(clone_path + '/README.mdown', 'w') as f:
        f.write('New readme')
    result = git.diff(clone_path)

    assert_in('a/README.mdown', result)
    assert_in('b/README.mdown', result)
    assert_in('+New readme', result)
    assert_in('-# Lint Review', result)


def test_apply_cached():
    assert False


def test_apply_cached__empty():
    assert False


def test_apply_cached__bad_patch():
    assert False


def test_commit():
    assert False


def test_push():
    assert False


def test_push__fails():
    assert False


def test_add_remote():
    assert False
