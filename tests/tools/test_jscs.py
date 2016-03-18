from lintreview.review import Problems
from lintreview.review import Comment
from lintreview.tools.jscs import Jscs
from lintreview.utils import in_path
from lintreview.utils import npm_exists
from unittest import TestCase
from unittest import skipIf
from nose.tools import eq_

jscs_missing = not(in_path('jscs') or npm_exists('jscs'))


class TestJcs(TestCase):

    needs_jscs = skipIf(jscs_missing, 'Needs jscs to run')

    fixtures = [
        'tests/fixtures/jscs/no_errors.js',
        'tests/fixtures/jscs/has_errors.js',
    ]

    def setUp(self):
        self.problems = Problems()
        self.tool = Jscs(self.problems)

    def test_match_file(self):
        self.assertFalse(self.tool.match_file('test.php'))
        self.assertFalse(self.tool.match_file('dir/name/test.py'))
        self.assertFalse(self.tool.match_file('test.py'))
        self.assertTrue(self.tool.match_file('test.js'))
        self.assertTrue(self.tool.match_file('dir/name/test.js'))

    @needs_jscs
    def test_check_dependencies(self):
        self.assertTrue(self.tool.check_dependencies())

    @needs_jscs
    def test_process_files__one_file_pass(self):
        self.tool.process_files([self.fixtures[0]])
        eq_([], self.problems.all(self.fixtures[0]))

    @needs_jscs
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

    @needs_jscs
    def test_process_files_two_files(self):
        self.tool.process_files(self.fixtures)

        eq_([], self.problems.all(self.fixtures[0]))

        problems = self.problems.all(self.fixtures[1])
        eq_(8, len(problems))

    @needs_jscs
    def test_process_files_with_config(self):
        config = {
            'preset': 'airbnb'
        }
        tool = Jscs(self.problems, config)
        tool.process_files([self.fixtures[0]])

        problems = self.problems.all(self.fixtures[0])

        eq_(1, len(problems))
