from __future__ import absolute_import
from lintreview.review import Problems
from lintreview.review import Comment
from lintreview.tools.jscs import Jscs
from unittest import TestCase
from nose.tools import eq_
from tests import root_dir, requires_image


class TestJscs(TestCase):

    fixtures = [
        'tests/fixtures/jscs/no_errors.js',
        'tests/fixtures/jscs/has_errors.js',
    ]

    def setUp(self):
        self.problems = Problems()
        self.tool = Jscs(self.problems, {}, root_dir)

    def test_match_file(self):
        self.assertFalse(self.tool.match_file('test.php'))
        self.assertFalse(self.tool.match_file('dir/name/test.py'))
        self.assertFalse(self.tool.match_file('test.py'))
        self.assertTrue(self.tool.match_file('test.js'))
        self.assertTrue(self.tool.match_file('dir/name/test.js'))

    @requires_image('nodejs')
    def test_check_dependencies(self):
        self.assertTrue(self.tool.check_dependencies())

    @requires_image('nodejs')
    def test_process_files__one_file_pass(self):
        self.tool.process_files([self.fixtures[0]])
        eq_([], self.problems.all(self.fixtures[0]))

    @requires_image('nodejs')
    def test_process_files__one_file_fail(self):
        self.tool.process_files([self.fixtures[1]])
        problems = self.problems.all(self.fixtures[1])
        eq_(8, len(problems))

        fname = self.fixtures[1]
        expected = Comment(
            fname, 1, 1, 'Illegal space before opening round brace')
        eq_(expected, problems[0])

        expected = Comment(fname, 7, 7, 'Expected indentation of 4 characters')
        eq_(expected, problems[6])

    @requires_image('nodejs')
    def test_process_files_two_files(self):
        self.tool.process_files(self.fixtures)

        eq_([], self.problems.all(self.fixtures[0]))

        problems = self.problems.all(self.fixtures[1])
        eq_(8, len(problems))

    @requires_image('nodejs')
    def test_process_files_with_config(self):
        config = {
            'preset': 'airbnb'
        }
        tool = Jscs(self.problems, config, root_dir)
        tool.process_files([self.fixtures[0]])

        problems = self.problems.all(self.fixtures[0])

        eq_(1, len(problems))
