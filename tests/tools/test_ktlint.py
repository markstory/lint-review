from __future__ import absolute_import
from unittest import TestCase

from lintreview.review import Problems, Comment
from lintreview.tools.ktlint import Ktlint
from tests import root_dir, requires_image
from nose.tools import eq_


FILE_WITH_NO_ERRORS = 'tests/fixtures/ktlint/no_errors.kt',
FILE_WITH_ERRORS = 'tests/fixtures/ktlint/has_errors.kt'


class TestKtlint(TestCase):

    def setUp(self):
        self.problems = Problems()
        options = {}
        self.tool = Ktlint(self.problems, options, root_dir)

    def test_match_file(self):
        self.assertFalse(self.tool.match_file('test.rb'))
        self.assertFalse(self.tool.match_file('dir/name/test.py'))
        self.assertFalse(self.tool.match_file('test.py'))
        self.assertTrue(self.tool.match_file('test.kt'))
        self.assertTrue(self.tool.match_file('dir/name/test.kt'))
        self.assertTrue(self.tool.match_file('test.kts'))

    @requires_image('ktlint')
    def test_check_dependencies(self):
        self.assertTrue(self.tool.check_dependencies())

    @requires_image('ktlint')
    def test_process_files_pass(self):
        self.tool.process_files(FILE_WITH_NO_ERRORS)
        eq_([], self.problems.all(FILE_WITH_NO_ERRORS))

    @requires_image('ktlint')
    def test_process_files_fail(self):
        self.tool.process_files([FILE_WITH_ERRORS])
        problems = self.problems.all(FILE_WITH_ERRORS)
        eq_(2, len(problems))

        expected = Comment(FILE_WITH_ERRORS, 1, 1, 'Redundant "toString()" call in string template')
        eq_(expected, problems[0])
        expected = Comment(FILE_WITH_ERRORS, 2, 2, 'Redundant curly braces')
        eq_(expected, problems[1])
