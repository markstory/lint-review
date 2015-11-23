import lintreview.git as git
import os
from test_github import config
from nose.tools import eq_
from nose.tools import raises
from unittest import skipIf

settings = {
    'WORKSPACE': './tests'
}

cant_write_to_test = not(os.access(os.path.abspath('./tests'), os.W_OK))


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
    path = settings['WORKSPACE'] + '/test_clone'
    git.clone(
        'git://github.com/markstory/it will never work.git',
        path)


@skipIf(cant_write_to_test, 'Cannot write to ./tests skipping')
def test_repo_operations():
    path = settings['WORKSPACE'] + '/test_clone'

    assert not(git.exists(path)), 'Directory should not exist.'
    res = git.clone(
        'git://github.com/markstory/lint-review.git',
        path)
    assert res, 'Cloned successfully.'
    assert git.exists(path), 'Cloned dir should be there.'
    git.destroy(path)
    assert not(git.exists(path)), 'Cloned dir should be gone.'


@skipIf(cant_write_to_test, 'Cannot write to ./tests skipping')
def test_clone_or_update():
    path = settings['WORKSPACE'] + '/test_clone'

    assert not(git.exists(path)), 'Directory should not exist.'
    git.clone_or_update(
        config,
        'git://github.com/markstory/lint-review.git',
        path,
        'e4f880c77e6b2c81c81cad5d45dd4e1c39b919a0')
    assert git.exists(path)
    git.destroy(path)
