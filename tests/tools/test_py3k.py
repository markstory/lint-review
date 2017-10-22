from __future__ import absolute_import
from unittest import TestCase, skipIf

from nose.tools import eq_

from lintreview.review import Problems
from lintreview.review import Comment
from lintreview.tools.py3k import Py3k
import sys

not_python2 = sys.version_info[0] >= 3


class TestPy3k(TestCase):

    needs_py2 = skipIf(not_python2, 'Cannot run in python3')

    class fixtures:
        no_errors = 'tests/fixtures/py3k/no_errors.py'
        has_errors = 'tests/fixtures/py3k/has_errors.py'

    def setUp(self):
        self.problems = Problems()
        self.tool = Py3k(self.problems)

    def test_match_file(self):
        self.assertFalse(self.tool.match_file('test.php'))
        self.assertFalse(self.tool.match_file('test.js'))
        self.assertFalse(self.tool.match_file('dir/name/test.js'))
        self.assertTrue(self.tool.match_file('test.py'))
        self.assertTrue(self.tool.match_file('dir/name/test.py'))

    def test_process_files__one_file_pass(self):
        self.tool.process_files([self.fixtures.no_errors])
        eq_([], self.problems.all(self.fixtures.no_errors))

    @needs_py2
    def test_process_files__one_file_fail(self):
        self.tool.process_files([self.fixtures.has_errors])
        problems = self.problems.all(self.fixtures.has_errors)
        eq_(2, len(problems))

        fname = self.fixtures.has_errors
        eq_([
            Comment(fname, 6, 6, 'E1601 print statement used'),
            Comment(fname, 11, 11,
                    'W1638 range built-in referenced when not iterating')
        ], problems)

    @needs_py2
    def test_process_files_two_files(self):
        self.tool.process_files([self.fixtures.no_errors,
                                 self.fixtures.has_errors])

        eq_([], self.problems.all(self.fixtures.no_errors))

        problems = self.problems.all(self.fixtures.has_errors)
        eq_(2, len(problems))

        fname = self.fixtures.has_errors
        eq_([
            Comment(fname, 6, 6, 'E1601 print statement used'),
            Comment(fname, 11, 11,
                    'W1638 range built-in referenced when not iterating')
        ], problems)
