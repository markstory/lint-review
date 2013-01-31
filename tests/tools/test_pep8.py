from lintreview.review import Review
from lintreview.tools.pep8 import Pep8
from unittest import TestCase
from nose.tools import eq_


class TestPep8(TestCase):

    fixtures = [
        'tests/fixtures/pep8/no_errors.py',
        'tests/fixtures/pep8/has_errors.py',
    ]

    def setUp(self):
        self.review = Review(None)
        self.tool = Pep8(self.review)

    def test_match_file(self):
        self.assertFalse(self.tool.match_file('test.php'))
        self.assertFalse(self.tool.match_file('test.js'))
        self.assertFalse(self.tool.match_file('dir/name/test.js'))
        self.assertTrue(self.tool.match_file('test.py'))
        self.assertTrue(self.tool.match_file('dir/name/test.py'))

    def test_process_files__one_file_pass(self):
        self.tool.process_files([self.fixtures[0]])
        eq_(None, self.review.problems(self.fixtures[0]))

    def test_process_files__one_file_fail(self):
        self.tool.process_files([self.fixtures[1]])
        problems = self.review.problems(self.fixtures[1])
        eq_(6, len(problems))
        expected = (2, 'E401 multiple imports on one line')
        eq_(expected, problems[0])

        expected = (11, "W603 '<>' is deprecated, use '!='")
        eq_(expected, problems[5])

    def test_process_files_two_files(self):
        self.tool.process_files(self.fixtures)

        eq_(None, self.review.problems(self.fixtures[0]))

        problems = self.review.problems(self.fixtures[1])
        eq_(6, len(problems))
        expected = (2, 'E401 multiple imports on one line')
        eq_(expected, problems[0])

        expected = (11, "W603 '<>' is deprecated, use '!='")
        eq_(expected, problems[5])

    def test_config_options_and_process_file(self):
        options = {
            'ignore': 'E2,W603'
        }
        self.tool = Pep8(self.review, options)
        self.tool.process_files([self.fixtures[1]])
        problems = self.review.problems(self.fixtures[1])
        eq_(4, len(problems))
        for p in problems:
            self.assertFalse('E2' in p)
            self.assertFalse('W603' in p)
