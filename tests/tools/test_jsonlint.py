from __future__ import absolute_import
from lintreview.review import Problems
from lintreview.review import Comment
from lintreview.tools.jsonlint import Jsonlint
from unittest import TestCase
from nose.tools import eq_, assert_in


class TestJsonlint(TestCase):

    fixtures = [
        'tests/fixtures/jsonlint/no_errors.json',
        'tests/fixtures/jsonlint/has_warnings.json',
        'tests/fixtures/jsonlint/has_errors.json',
    ]

    def setUp(self):
        self.problems = Problems()
        self.tool = Jsonlint(self.problems)

    def test_match_file(self):
        self.assertFalse(self.tool.match_file('test.php'))
        self.assertFalse(self.tool.match_file('test.js'))
        self.assertFalse(self.tool.match_file('dir/name/test.js'))
        self.assertTrue(self.tool.match_file('test.json'))
        self.assertTrue(self.tool.match_file('dir/name/test.json'))

    def test_process_files__one_file_pass(self):
        self.tool.process_files([self.fixtures[0]])
        eq_([], self.problems.all(self.fixtures[0]))

    def test_process_files__one_file_fail(self):
        self.tool.process_files([self.fixtures[1]])
        problems = self.problems.all(self.fixtures[1])
        eq_(2, len(problems))

        fname = self.fixtures[1]

        msg = ("Warning: String literals must use "
               "double quotation marks in strict JSON")
        expected = Comment(fname, 2, 2, msg)
        eq_(expected, problems[0])

        msg = ("Warning: JSON does not allow identifiers "
               "to be used as strings: u'three'\n"
               "Warning: Strict JSON does not allow a final comma "
               "in an object (dictionary) literal")
        eq_(3, problems[1].line)
        eq_(3, problems[1].position)
        assert_in("Warning: JSON does not allow identifiers",
                  problems[1].body)
        assert_in("Warning: Strict JSON does not allow a final comma",
                  problems[1].body)

    def test_process_files_three_files(self):
        self.tool.process_files(self.fixtures)

        eq_([], self.problems.all(self.fixtures[0]))

        fname = self.fixtures[1]
        problems = self.problems.all(fname)
        eq_(2, len(problems))

        msg = ("Warning: String literals must use "
               "double quotation marks in strict JSON")
        expected = Comment(fname, 2, 2, msg)
        eq_(expected, problems[0])

        eq_(3, problems[1].line)
        eq_(3, problems[1].position)
        assert_in('JSON does not allow identifiers to be used',
                  problems[1].body)

        fname = self.fixtures[2]
        problems = self.problems.all(fname)
        eq_(1, len(problems))

        eq_(1, problems[0].line)
        eq_(1, problems[0].position)
        assert_in('Unknown identifier', problems[0].body)
