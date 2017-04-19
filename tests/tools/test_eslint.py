from unittest import TestCase
from unittest import skipIf

from lintreview.review import Problems
from lintreview.review import Comment, IssueComment
from lintreview.tools.eslint import Eslint
from lintreview.utils import in_path
from lintreview.utils import npm_exists
from nose.tools import eq_, ok_

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
        self.assertTrue(self.tool.match_file('test.jsx'))
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

        msg = ("'foo' is assigned a value but never used. (no-unused-vars)\n"
               "'bar' is not defined. (no-undef)")
        expected = Comment(FILE_WITH_ERRORS, 2, 2, msg)
        eq_(expected, problems[0])

        msg = ("'alert' is not defined. (no-undef)")
        expected = Comment(FILE_WITH_ERRORS, 4, 4, msg)
        eq_(expected, problems[1])

    @needs_eslint
    def test_process_files__config_file_missing(self):
        tool = Eslint(self.problems, options={'config': 'invalid-file'})
        tool.process_files([FILE_WITH_ERRORS])
        problems = self.problems.all()
        eq_(1, len(problems), 'Invalid config returns 1 error')
        msg = ('Your eslint config file is missing or invalid. '
               'Please ensure that `invalid-file` exists and is valid.')
        expected = [IssueComment(msg)]
        eq_(expected, problems)

    @needs_eslint
    def test_process_files_uses_default_config(self):
        tool = Eslint(self.problems, options={})
        tool.process_files([FILE_WITH_ERRORS])
        problems = self.problems.all(FILE_WITH_ERRORS)
        eq_(2, len(problems), 'With no config file there should be no errors.')

    @needs_eslint
    def test_process_files__invalid_config(self):
        options = {'config': 'tests/fixtures/eslint/invalid.json'}
        tool = Eslint(self.problems, options)
        tool.process_files([FILE_WITH_ERRORS])
        problems = self.problems.all()
        eq_(1, len(problems), 'Invalid config should report an error')
        error = problems[0]
        ok_('Your eslint configuration output the following error'
            in error.body)
        ok_("Cannot find module 'eslint-config-invalid-rules'"
            in error.body)
        ok_("Referenced from" in error.body)

    @needs_eslint
    def test_process_files_with_config(self):
        options = {
            'config': 'tests/fixtures/eslint/config.json'
        }
        tool = Eslint(self.problems, options)
        tool.process_files([FILE_WITH_ERRORS])

        problems = self.problems.all(FILE_WITH_ERRORS)

        msg = ("'foo' is assigned a value but never used. (no-unused-vars)\n"
               "'bar' is not defined. (no-undef)\n"
               "Missing semicolon. (semi)")
        expected = [Comment(FILE_WITH_ERRORS, 2, 2, msg)]
        eq_(expected, problems)
