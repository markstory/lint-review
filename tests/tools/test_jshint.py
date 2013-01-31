from lintreview.review import Review
from lintreview.tools.jshint import Jshint
from lintreview.utils import in_path
from unittest import TestCase
from unittest import skipIf
from nose.tools import eq_

jshint_missing = not(in_path('jshint'))


class TestJshint(TestCase):

    fixtures = [
        'tests/fixtures/jshint/no_errors.js',
        'tests/fixtures/jshint/has_errors.js',
    ]

    def setUp(self):
        self.review = Review({})
        self.tool = Jshint(self.review)

    def test_match_file(self):
        self.assertFalse(self.tool.match_file('test.php'))
        self.assertFalse(self.tool.match_file('dir/name/test.py'))
        self.assertFalse(self.tool.match_file('test.py'))
        self.assertTrue(self.tool.match_file('test.js'))
        self.assertTrue(self.tool.match_file('dir/name/test.js'))

    @skipIf(jshint_missing, 'Missing jshint, cannot run')
    def test_check_dependencies(self):
        self.assertTrue(self.tool.check_dependencies())

    @skipIf(jshint_missing, 'Missing jshint, cannot run')
    def test_process_files__one_file_pass(self):
        self.tool.process_files([self.fixtures[0]])
        eq_(None, self.review.problems(self.fixtures[0]))

    @skipIf(jshint_missing, 'Missing jshint, cannot run')
    def test_process_files__one_file_fail(self):
        self.tool.process_files([self.fixtures[1]])
        problems = self.review.problems(self.fixtures[1])
        eq_(13, len(problems))

        expected = (1, 'Missing name in function declaration.')
        eq_(expected, problems[0])

        expected = (6, "Use '===' to compare with 'null'.")
        eq_(expected, problems[2])

    @skipIf(jshint_missing, 'Missing jshint, cannot run')
    def test_process_files_two_files(self):
        self.tool.process_files(self.fixtures)

        eq_(None, self.review.problems(self.fixtures[0]))

        problems = self.review.problems(self.fixtures[1])
        eq_(13, len(problems))
