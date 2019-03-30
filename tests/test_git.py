from __future__ import absolute_import
import os
from unittest import TestCase
from mock import patch

import lintreview.git as git
from .test_github import config
from . import (
    setup_repo,
    teardown_repo,
    clone_path,
    cant_write_to_test
)
from unittest import skipIf

settings = {
    'WORKSPACE': os.path.join(clone_path, '/tests')
}


class TestGit(TestCase):

    def setUp(self):
        setup_repo()

    def tearDown(self):
        teardown_repo()

    def test_get_repo_path(self):
        user = 'markstory'
        repo = 'asset_compress'
        num = '4'
        res = git.get_repo_path(user, repo, num, settings)
        expected = os.sep.join(
            (settings['WORKSPACE'], user, repo, num))
        expected = os.path.realpath(expected)
        self.assertEqual(res, expected)

    def test_get_repo_path__int(self):
        user = 'markstory'
        repo = 'asset_compress'
        num = 4
        res = git.get_repo_path(user, repo, num, settings)
        expected = os.sep.join(
            (settings['WORKSPACE'], user, repo, str(num)))
        expected = os.path.realpath(expected)
        self.assertEqual(res, expected)

    def test_get_repo_path__absoulte_dir(self):
        user = 'markstory'
        repo = 'asset_compress'
        num = 4
        settings['WORKSPACE'] = os.path.realpath(settings['WORKSPACE'])
        res = git.get_repo_path(user, repo, num, settings)
        expected = os.sep.join(
            (settings['WORKSPACE'], user, repo, str(num)))
        expected = os.path.realpath(expected)
        self.assertEqual(res, expected)

    def test_exists__no_path(self):
        assert not git.exists(settings['WORKSPACE'] + '/herp/derp')

    def test_exists__no_git(self):
        assert not git.exists(settings['WORKSPACE'])

    def test_repo_clone_no_repo(self):
        self.assertRaises(IOError,
                          git.clone,
                          'git://github.com/markstory/it will never work.git',
                          clone_path)

    @skipIf(cant_write_to_test, 'Cannot write to ./tests skipping')
    def test_repo_operations(self):
        teardown_repo()
        res = git.clone(
            'git://github.com/markstory/lint-review.git',
            clone_path)
        assert res, 'Cloned successfully.'
        assert git.exists(clone_path), 'Cloned dir should be there.'
        git.destroy(clone_path)
        assert not(git.exists(clone_path)), 'Cloned dir should be gone.'

    @skipIf(cant_write_to_test, 'Cannot write to ./tests skipping')
    @patch('lintreview.git.checkout')
    @patch('lintreview.git.fetch')
    def test_clone_or_update(self, mock_fetch, mock_checkout):
        teardown_repo()
        git.clone_or_update(
            config,
            'git://github.com/markstory/lint-review.git',
            clone_path,
            'e4f880c77e6b2c81c81cad5d45dd4e1c39b919a0')
        assert git.exists(clone_path)

    @skipIf(cant_write_to_test, 'Cannot write to ./tests skipping')
    def test_diff(self):
        with open(clone_path + '/README.mdown', 'w') as f:
            f.write('New readme')
        result = git.diff(clone_path)

        self.assertIn('a/README.mdown', result)
        self.assertIn('b/README.mdown', result)
        self.assertIn('+New readme', result)
        self.assertIn('-# Lint Review', result)

    @skipIf(cant_write_to_test, 'Cannot write to ./tests skipping')
    def test_diff__files_list(self):
        with open(clone_path + '/README.mdown', 'w') as f:
            f.write('New readme')
        result = git.diff(clone_path, ['LICENSE'])
        self.assertEqual('', result)

    @skipIf(cant_write_to_test, 'Cannot write to ./tests skipping')
    def test_diff__non_git_path(self):
        path = os.path.abspath(clone_path + '/../../../')
        self.assertRaises(
            IOError,
            git.diff,
            path
        )

    @skipIf(cant_write_to_test, 'Cannot write to ./tests skipping')
    def test_apply_cached(self):
        with open(clone_path + '/README.mdown', 'w') as f:
            f.write('New readme')
        # Get the initial diff.
        diff = git.diff(clone_path)
        git.apply_cached(clone_path, diff)

        # Changes have been staged, diff result should be empty.
        diff = git.diff(clone_path)
        self.assertEqual(diff, '')

    @skipIf(cant_write_to_test, 'Cannot write to ./tests skipping')
    def test_apply_cached__empty(self):
        git.apply_cached(clone_path, '')

        # No changes, no diff.
        diff = git.diff(clone_path)
        self.assertEqual(diff, '')

    @skipIf(cant_write_to_test, 'Cannot write to ./tests skipping')
    def test_apply_cached__bad_patch(self):
        self.assertRaises(
            IOError,
            git.apply_cached,
            clone_path,
            'not a diff'
        )

    @skipIf(cant_write_to_test, 'Cannot write to ./tests skipping')
    def test_apply_cached__non_git_path(self):
        path = os.path.abspath(clone_path + '/../../')
        self.assertRaises(
            IOError,
            git.apply_cached,
            path,
            'not a patch'
        )

    @skipIf(cant_write_to_test, 'Cannot write to ./tests skipping')
    def test_commit_and_status(self):
        with open(clone_path + '/README.mdown', 'w') as f:
            f.write('New readme')
        diff = git.diff(clone_path)

        status = git.status(clone_path)
        assert 'README.mdown' in status

        git.apply_cached(clone_path, diff)
        git.commit(clone_path, 'robot <bot@example.com>', 'Fixed readme')
        status = git.status(clone_path)
        self.assertEqual('', status, 'No changes unstaged, or uncommitted')

    @skipIf(cant_write_to_test, 'Cannot write to ./tests skipping')
    def test_add_remote(self):
        output = git.add_remote(
            clone_path,
            'testing',
            'git://github.com/markstory/lint-review.git')
        self.assertEqual('', output)

    @skipIf(cant_write_to_test, 'Cannot write to ./tests skipping')
    def test_add_remote__duplicate(self):
        try:
            git.add_remote(
                clone_path,
                'origin',
                'git://github.com/markstory/lint-review.git')
        except IOError as e:
            self.assertIn('Unable to add remote origin', str(e))

    @skipIf(cant_write_to_test, 'Cannot write to ./tests skipping')
    def test_push__fails(self):
        try:
            git.push(clone_path, 'origin', 'master')
        except IOError as e:
            self.assertIn('origin:master', str(e))

    @skipIf(cant_write_to_test, 'Cannot write to ./tests skipping')
    def test_create_branch(self):
        git.create_branch(clone_path, 'testing')
        self.assertEqual(True, git.branch_exists(clone_path, 'master'))
        self.assertEqual(True, git.branch_exists(clone_path, 'testing'))
        self.assertEqual(False, git.branch_exists(clone_path, 'nope'))

    @skipIf(cant_write_to_test, 'Cannot write to ./tests skipping')
    def test_destroy_unicode_paths(self):
        full_clone_path = os.path.join(clone_path, "\u2620.txt")
        with open(full_clone_path, 'w') as f:
            f.write('skull and crossbones')

        git.destroy(clone_path)
