from unittest import TestCase
from unittest import skipIf

from lintreview.review import Problems
from lintreview.review import Comment
from lintreview.tools.eslint import Eslint
from lintreview.utils import in_path
from lintreview.utils import npm_exists
from nose.tools import eq_

eslint_missing = not(in_path('eslint') or npm_exists('eslint'))

FILE_WITH_NO_ERRORS = 'tests/fixtures/eslint/no_errors.js',
FILE_WITH_ERRORS = 'tests/fixtures/eslint/has_errors.js'


class TestEslint(TestCase):

    needs_eslint = skipIf(eslint_missing, 'Needs eslint to run')

    def setUp(self):
        self.problems = Problems()
        options = {
            'config': 'tests/fixtures/eslint/recommended_config.json'
        }
        self.tool = Eslint(self.problems, options)

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
        self.tool.process_files(FILE_WITH_NO_ERRORS)
        eq_([], self.problems.all(FILE_WITH_NO_ERRORS))

    @needs_eslint
    def test_process_files_fail(self):
        self.tool.process_files([FILE_WITH_ERRORS])
        problems = self.problems.all(FILE_WITH_ERRORS)
        eq_(2, len(problems))

        msg = ("'foo' is defined but never used (no-unused-vars)\n"
               "'bar' is not defined. (no-undef)")
        expected = Comment(FILE_WITH_ERRORS, 2, 2, msg)
        eq_(expected, problems[0])

        msg = ("'alert' is not defined. (no-undef)")
        expected = Comment(FILE_WITH_ERRORS, 4, 4, msg)
        eq_(expected, problems[1])

    @needs_eslint
    def test_process_files_with_no_config(self):
        tool = Eslint(self.problems, options={})
        tool.process_files([FILE_WITH_ERRORS])
        problems = self.problems.all(FILE_WITH_ERRORS)
        eq_(0, len(problems), 'With no config file there should be no errors.')

    @needs_eslint
    def test_process_files_with_config(self):
        options = {
            'config': 'tests/fixtures/eslint/config.json'
        }
        tool = Eslint(self.problems, options)
        tool.process_files([FILE_WITH_ERRORS])

        problems = self.problems.all(FILE_WITH_ERRORS)

        msg = ("'foo' is defined but never used (no-unused-vars)\n"
               "'bar' is not defined. (no-undef)\n"
               "Missing semicolon. (semi)")
        expected = [Comment(FILE_WITH_ERRORS, 2, 2, msg)]
        eq_(expected, problems)
