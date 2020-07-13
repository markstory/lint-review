from unittest import TestCase
from lintreview.review import Problems, Comment
from lintreview.tools.standardjs import Standardjs
from tests import root_dir, requires_image

FILE_WITH_NO_ERRORS = 'tests/fixtures/standardjs/no_errors.js',
FILE_WITH_ERRORS = 'tests/fixtures/standardjs/has_errors.js'


class TestStandardjs(TestCase):

    def setUp(self):
        self.problems = Problems()
        options = {}
        self.tool = Standardjs(self.problems, options, root_dir)

    def test_version(self):
        assert self.tool.version != ''

    def test_match_file(self):
        self.assertFalse(self.tool.match_file('test.php'))
        self.assertFalse(self.tool.match_file('dir/name/test.py'))
        self.assertFalse(self.tool.match_file('test.py'))
        self.assertTrue(self.tool.match_file('test.js'))
        self.assertTrue(self.tool.match_file('dir/name/test.js'))

    @requires_image('nodejs')
    def test_check_dependencies(self):
        self.assertTrue(self.tool.check_dependencies())

    @requires_image('nodejs')
    def test_process_files_pass(self):
        self.tool.process_files(FILE_WITH_NO_ERRORS)
        self.assertEqual([], self.problems.all(FILE_WITH_NO_ERRORS))

    @requires_image('nodejs')
    def test_process_files_fail(self):
        self.tool.process_files([FILE_WITH_ERRORS])
        problems = self.problems.all(FILE_WITH_ERRORS)
        self.assertEqual(2, len(problems))

        msg = ("'foo' is assigned a value but never used.\n"
               "'bar' is not defined.")
        expected = Comment(FILE_WITH_ERRORS, 2, 2, msg)
        self.assertEqual(expected, problems[0])

        msg = ("'alert' is not defined.\n"
               'Strings must use singlequote.\n'
               'Extra semicolon.')
        expected = Comment(FILE_WITH_ERRORS, 4, 4, msg)
        self.assertEqual(expected, problems[1])
