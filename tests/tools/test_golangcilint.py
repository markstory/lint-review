from __future__ import absolute_import

from lintreview.review import Problems, Comment
from lintreview.tools.golangcilint import Golangcilint
from unittest import TestCase
from nose.tools import eq_, assert_in
from tests import requires_image, test_dir

import os.path


class TestGolangcilint(TestCase):

    fixtures = [
        'no_errors.go',
        'has_errors.go',
    ]

    def setUp(self):
        self.fixture_path = os.path.join(test_dir, 'fixtures', 'golangcilint')
        self.problems = Problems()
        self.tool = Golangcilint(self.problems, {}, self.fixture_path)

    def test_match_file(self):
        self.assertTrue(self.tool.match_file('test.go'))
        self.assertTrue(self.tool.match_file('dir/name/test.go'))
        self.assertFalse(self.tool.match_file('dir/name/test.py'))
        self.assertFalse(self.tool.match_file('test.php'))
        self.assertFalse(self.tool.match_file('test.golp'))

    @requires_image('golint')
    def test_check_dependencies(self):
        self.assertTrue(self.tool.check_dependencies())

    @requires_image('golint')
    def test_process_files__one_file_pass(self):
        self.tool.process_files([self.fixtures[0]])
        eq_([], self.problems.all(self.fixtures[0]))

    @requires_image('golint')
    def test_process_files__one_file_fail(self):
        self.tool.process_files([self.fixtures[1]])
        problems = self.problems.all(self.fixtures[1])
        eq_(3, len(problems))

        fname = self.fixtures[1]
        expected = Comment(
            fname,
            9,
            9,
            'method is missing receiver (typecheck)')
        eq_(expected, problems[0])

    @requires_image('golint')
    def test_process_files_two_files(self):
        self.tool.process_files([self.fixtures[0], self.fixtures[1]])

        warning = self.problems.all()[0]
        assert_in('Golangci-lint emit the following warnings:', warning.body)
        assert_in('megacheck', warning.body)

        eq_([], self.problems.all(self.fixtures[0]))

        problems = self.problems.all(self.fixtures[1])
        eq_(3, len(problems))
        first = problems[0]
        assert_in('method is missing receiver (typecheck)', first.body)

    @requires_image('golint')
    def test_process_files_with_config(self):
        config = {
            'config': 'golangci.yml'
        }
        tool = Golangcilint(self.problems, config, self.fixture_path)
        tool.process_files([self.fixtures[1]])
        eq_(3, len(self.problems))

    @requires_image('golint')
    def test_process_files_with_corrupt_config(self):
        config = {
            'config': 'corrupt.yml'
        }
        tool = Golangcilint(self.problems, config, self.fixture_path)
        tool.process_files([self.fixtures[1]])
        eq_(1, len(self.problems))
        error = self.problems.all()[0]
        assert_in(
            'Golangci-lint failed and output the following:\n',
            error.body
        )
        assert_in("Can't read config", error.body)

    @requires_image('golint')
    def test_process_files_with_missing_config(self):
        config = {
            'config': 'not/found.yml'
        }
        tool = Golangcilint(self.problems, config, self.fixture_path)
        tool.process_files([self.fixtures[1]])
        eq_(1, len(self.problems))
        error = self.problems.all()[0]
        assert_in(
            'Golangci-lint failed and output the following:\n',
            error.body
        )
        assert_in("Can't read config", error.body)

    def test_has_fixer__not_enabled(self):
        tool = Golangcilint(self.problems, {})
        eq_(False, tool.has_fixer())
