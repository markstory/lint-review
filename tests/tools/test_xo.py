from unittest import TestCase
from unittest import skipIf

from lintreview.review import Problems
from lintreview.review import Comment
from lintreview.tools.xo import Xo
from lintreview.utils import in_path
from lintreview.utils import npm_exists
from nose.tools import eq_

xo_missing = not(in_path('xo') or npm_exists('xo'))

FILE_WITH_NO_ERRORS = 'tests/samples/xo/no_errors.js',
FILE_WITH_ERRORS = 'tests/samples/xo/has_errors.js'


class TestXo(TestCase):

    needs_xo = skipIf(xo_missing, 'Needs xo to run')

    def setUp(self):
        self.problems = Problems()
        options = {
            'ignore': ''
        }
        self.tool = Xo(self.problems, options)

    def test_match_file(self):
        self.assertFalse(self.tool.match_file('test.php'))
        self.assertFalse(self.tool.match_file('dir/name/test.py'))
        self.assertFalse(self.tool.match_file('test.py'))
        self.assertTrue(self.tool.match_file('test.js'))
        self.assertTrue(self.tool.match_file('test.jsx'))
        self.assertTrue(self.tool.match_file('dir/name/test.js'))

    @needs_xo
    def test_check_dependencies(self):
        self.assertTrue(self.tool.check_dependencies())

    @needs_xo
    def test_process_files_pass(self):
        self.tool.process_files(FILE_WITH_NO_ERRORS)
        eq_([], self.problems.all(FILE_WITH_NO_ERRORS))

    @needs_xo
    def test_process_files_fail(self):
        self.tool.process_files([FILE_WITH_ERRORS])
        problems = self.problems.all(FILE_WITH_ERRORS)
        eq_(2, len(problems))

        msg = ("Filename is not in kebab case. Rename it to `has-errors.js`."
               " (unicorn/filename-case)\n"
               "Unexpected var, use let or const instead. (no-var)\n"
               "'foo' is assigned a value but never used. (no-unused-vars)\n"
               "'bar' is not defined. (no-undef)\n"
               "Missing semicolon. (semi)")
        expected = Comment(FILE_WITH_ERRORS, 2, 2, msg)
        eq_(expected, problems[0])

        msg = ("Unexpected alert. (no-alert)\n"
               "'alert' is not defined. (no-undef)\n"
               "Strings must use singlequote. (quotes)")
        expected = Comment(FILE_WITH_ERRORS, 4, 4, msg)
        eq_(expected, problems[1])
