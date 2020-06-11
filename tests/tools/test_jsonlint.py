from lintreview.review import Problems, Comment
from lintreview.tools.jsonlint import Jsonlint
from unittest import TestCase
from tests import root_dir, requires_image


class TestJsonlint(TestCase):

    fixtures = [
        'tests/fixtures/jsonlint/no_errors.json',
        'tests/fixtures/jsonlint/has_warnings.json',
        'tests/fixtures/jsonlint/has_errors.json',
    ]

    def setUp(self):
        self.problems = Problems()
        self.tool = Jsonlint(self.problems, {}, root_dir)

    def test_match_file(self):
        self.assertFalse(self.tool.match_file('test.php'))
        self.assertFalse(self.tool.match_file('test.js'))
        self.assertFalse(self.tool.match_file('dir/name/test.js'))
        self.assertTrue(self.tool.match_file('test.json'))
        self.assertTrue(self.tool.match_file('dir/name/test.json'))

    @requires_image('python2')
    def test_process_files__one_file_pass(self):
        self.tool.process_files([self.fixtures[0]])
        self.assertEqual([], self.problems.all(self.fixtures[0]))

    @requires_image('python2')
    def test_process_files__one_file_fail(self):
        self.tool.process_files([self.fixtures[1]])
        problems = self.problems.all(self.fixtures[1])
        self.assertEqual(2, len(problems))

        fname = self.fixtures[1]

        msg = ("Warning: String literals must use "
               "double quotation marks in strict JSON")
        expected = Comment(fname, 2, 2, msg)
        self.assertEqual(expected, problems[0])

        msg = ("Warning: JSON does not allow identifiers "
               "to be used as strings: u'three'\n"
               "Warning: Strict JSON does not allow a final comma "
               "in an object (dictionary) literal")
        self.assertEqual(3, problems[1].line)
        self.assertEqual(3, problems[1].position)
        self.assertIn("Warning: JSON does not allow identifiers",
                      problems[1].body)
        self.assertIn("Warning: Strict JSON does not allow a final comma",
                      problems[1].body)

    @requires_image('python2')
    def test_process_files_three_files(self):
        self.tool.process_files(self.fixtures)

        self.assertEqual([], self.problems.all(self.fixtures[0]))

        fname = self.fixtures[1]
        problems = self.problems.all(fname)
        self.assertEqual(2, len(problems))

        msg = ("Warning: String literals must use "
               "double quotation marks in strict JSON")
        expected = Comment(fname, 2, 2, msg)
        self.assertEqual(expected, problems[0])

        self.assertEqual(3, problems[1].line)
        self.assertEqual(3, problems[1].position)
        self.assertIn('JSON does not allow identifiers to be used',
                      problems[1].body)

        fname = self.fixtures[2]
        problems = self.problems.all(fname)
        self.assertEqual(1, len(problems))

        self.assertEqual(1, problems[0].line)
        self.assertEqual(1, problems[0].position)
        self.assertIn('Unknown identifier', problems[0].body)
