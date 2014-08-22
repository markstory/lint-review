from lintreview.review import Problems
from lintreview.review import Comment
from lintreview.tools.flake8 import Flake8
from unittest import TestCase
from nose.tools import eq_


class TestFlake8(TestCase):

    fixtures = [
        'tests/fixtures/pep8/no_errors.py',
        'tests/fixtures/pep8/has_errors.py',
    ]

    def setUp(self):
        self.problems = Problems()
        self.tool = Flake8(self.problems)

    def test_match_file(self):
        self.assertFalse(self.tool.match_file('test.php'))
        self.assertFalse(self.tool.match_file('test.js'))
        self.assertFalse(self.tool.match_file('dir/name/test.js'))
        self.assertTrue(self.tool.match_file('test.py'))
        self.assertTrue(self.tool.match_file('dir/name/test.py'))

    def test_process_files__one_file_pass(self):
        self.tool.process_files([self.fixtures[0]])
        eq_([], self.problems.all(self.fixtures[0]))

    def test_process_files__one_file_fail(self):
        self.tool.process_files([self.fixtures[1]])
        problems = self.problems.all(self.fixtures[1])
        eq_(8, len(problems))

        fname = self.fixtures[1]
        expected = Comment(fname, 2, 2, "F401 're' imported but unused")
        eq_(expected, problems[1])

        expected = Comment(fname, 11, 11, "W603 '<>' is deprecated, use '!='")
        eq_(expected, problems[7])

    def test_process_files_two_files(self):
        self.tool.process_files(self.fixtures)

        eq_([], self.problems.all(self.fixtures[0]))

        problems = self.problems.all(self.fixtures[1])
        eq_(8, len(problems))

        fname = self.fixtures[1]
        expected = Comment(fname, 2, 2, "F401 're' imported but unused")
        eq_(expected, problems[1])

        expected = Comment(fname, 11, 11, "W603 '<>' is deprecated, use '!='")
        eq_(expected, problems[7])

    def test_config_options_and_process_file(self):
        options = {
            'ignore': 'F4,W603'
        }
        self.tool = Flake8(self.problems, options)
        self.tool.process_files([self.fixtures[1]])
        problems = self.problems.all(self.fixtures[1])
        eq_(6, len(problems))
        for p in problems:
            self.assertFalse('F4' in p)
            self.assertFalse('W603' in p)
