from lintreview.review import Problems
from lintreview.review import Comment
from lintreview.tools.eslint import Eslint
from lintreview.utils import in_path
from lintreview.utils import npm_exists
from unittest import TestCase
from unittest import skipIf
from nose.tools import eq_

eslint_missing = not(in_path('eslint') or npm_exists('eslint'))

class TestEslint(TestCase):

    needs_eslint = skipIf(eslint_missing, 'Needs eslint to run')

    fixtures = [
        'tests/fixtures/eslint/no_errors.js',
        'tests/fixtures/eslint/has_errors.js'
    ]

    def setUp(self):
        self.problems = Problems()
        self.tool = Eslint(self.problems)

    def test_match_file(self):
        self.assertFalse(self.tool.match_file('test.php'))
        self.assertFalse(self.tool.match_file('dir/name/test.py'))
        self.assertFalse(self.tool.match_file('test.py'))
        self.assertTrue(self.tool.match_file('test.js'))
        self.assertTrue(self.tool.match_file('dir/name/test.js'))

    @needs_eslint
    def test_check_dependencies(self):
        self.assertTrue(self.tool.check_dependencies())

    @needs_eslint
    def test_process_files_pass(self):
        self.tool.process_files([self.fixtures[0]])
        eq_([], self.problems.all(self.fixtures[0]))

    @needs_eslint
    def test_process_files_fail(self):
        self.tool.process_files([self.fixtures[1]])
        problems = self.problems.all(self.fixtures[1])
        eq_(5, len(problems))

        fname = self.fixtures[1]
        expected = Comment(fname, 2, 2, 'foo is defined but never used (no-unused-vars)')
        eq_(expected, problems[0])

        expected = Comment(fname, 4, 4, '"alert" is not defined. (no-undef)')
        eq_(expected, problems[4])

    @needs_eslint
    def test_process_files_with_config(self):
        config = {
            'config': 'tests/fixtures/eslint/config.json'
        }
        tool = Eslint(self.problems, config)
        tool.process_files([self.fixtures[1]])

        problems = self.problems.all(self.fixtures[1])

        eq_(4, len(problems), 'Config file should lower error count.')
