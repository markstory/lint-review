import lintreview.git as git
import os
import shutil
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
