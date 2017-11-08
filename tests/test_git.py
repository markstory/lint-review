from __future__ import absolute_import
import lintreview.git as git
import os
from .test_github import config
from nose.tools import eq_, raises, assert_in, with_setup
from unittest import skipIf

settings = {
    'WORKSPACE': './tests'
}
clone_path = settings['WORKSPACE'] + '/test_clone'
cant_write_to_test = not(os.access(os.path.abspath('./tests'), os.W_OK))


def setup_repo():
    git.clone_or_update(
        config,
        'git://github.com/markstory/lint-review.git',
        clone_path,
        'master')


def teardown_repo():
    if git.exists(clone_path):
        git.destroy(clone_path)


def noop():
    pass


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
@with_setup(noop, teardown_repo)
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
@with_setup(noop, teardown_repo)
def test_clone_or_update():
    git.clone_or_update(
        config,
        'git://github.com/markstory/lint-review.git',
        clone_path,
        'e4f880c77e6b2c81c81cad5d45dd4e1c39b919a0')
    assert git.exists(clone_path)


@skipIf(cant_write_to_test, 'Cannot write to ./tests skipping')
@with_setup(setup_repo, teardown_repo)
def test_diff():
    with open(clone_path + '/README.mdown', 'w') as f:
        f.write('New readme')
    result = git.diff(clone_path)

    assert_in('a/README.mdown', result)
    assert_in('b/README.mdown', result)
    assert_in('+New readme', result)
    assert_in('-# Lint Review', result)


@skipIf(cant_write_to_test, 'Cannot write to ./tests skipping')
@raises(IOError)
def test_diff__non_git_path():
    git.diff(settings['WORKSPACE'] + '/../../')


@skipIf(cant_write_to_test, 'Cannot write to ./tests skipping')
@with_setup(setup_repo, teardown_repo)
def test_apply_cached():
    with open(clone_path + '/README.mdown', 'w') as f:
        f.write('New readme')
    # Get the initial diff.
    diff = git.diff(clone_path)
    git.apply_cached(clone_path, diff)

    # Changes have been staged, diff result should be empty.
    diff = git.diff(clone_path)
    eq_(diff, '')


@skipIf(cant_write_to_test, 'Cannot write to ./tests skipping')
@with_setup(setup_repo, teardown_repo)
def test_apply_cached__empty():
    git.apply_cached(clone_path, '')

    # No changes, no diff.
    diff = git.diff(clone_path)
    eq_(diff, '')


@skipIf(cant_write_to_test, 'Cannot write to ./tests skipping')
@raises(IOError)
@with_setup(setup_repo, teardown_repo)
def test_apply_cached__bad_patch():
    git.apply_cached(clone_path, 'not a diff')


@skipIf(cant_write_to_test, 'Cannot write to ./tests skipping')
@raises(IOError)
def test_apply_cached__non_git_path():
    git.apply_cached(settings['WORKSPACE'] + '/../../', 'not a patch')


@skipIf(cant_write_to_test, 'Cannot write to ./tests skipping')
@with_setup(setup_repo, teardown_repo)
def test_commit_and_status():
    with open(clone_path + '/README.mdown', 'w') as f:
        f.write('New readme')
    diff = git.diff(clone_path)

    status = git.status(clone_path)
    assert 'README.mdown' in status

    git.apply_cached(clone_path, diff)
    git.commit(clone_path, 'robot <bot@example.com>', 'Fixed readme')
    status = git.status(clone_path)
    eq_('', status, 'No changes unstaged, or uncommitted')


@skipIf(cant_write_to_test, 'Cannot write to ./tests skipping')
def test_push():
    assert False, 'not done'


@skipIf(cant_write_to_test, 'Cannot write to ./tests skipping')
def test_push__fails():
    assert False, 'not done'


@skipIf(cant_write_to_test, 'Cannot write to ./tests skipping')
def test_add_remote():
    assert False, 'not done'
