from lintreview.review import Problems, Comment
from lintreview.tools.mypy import Mypy
from unittest import TestCase
from tests import root_dir, requires_image


class TestMypy(TestCase):
    fixtures = [
        'tests/fixtures/mypy/no_errors.py',
        'tests/fixtures/mypy/has_errors.py',
    ]

    def setUp(self):
        self.problems = Problems()
        self.tool = Mypy(self.problems, {}, root_dir)

    def test_version(self):
        assert self.tool.version != ''

    def test_match_file(self):
        self.assertFalse(self.tool.match_file('test.php'))
        self.assertFalse(self.tool.match_file('test.js'))
        self.assertFalse(self.tool.match_file('dir/name/test.js'))
        self.assertTrue(self.tool.match_file('test.py'))
        self.assertTrue(self.tool.match_file('dir/name/test.py'))

    @requires_image('python3')
    def test_process_files__one_file_pass(self):
        self.tool.process_files([self.fixtures[0]])
        self.assertEqual([], self.problems.all(self.fixtures[0]))

    @requires_image('python3')
    def test_process_files__one_file_fail(self):
        self.tool.process_files([self.fixtures[1]])
        problems = self.problems.all(self.fixtures[1])
        self.assertEqual(3, len(problems))

        fname = self.fixtures[1]
        expected = Comment(fname, 7, 7, 'Incompatible types in assignment '
                           '(expression has type "List[int]", variable has type "int")')
        self.assertEqual(expected, problems[0])

        expected = Comment(fname, 8, 8, 'Incompatible types in assignment '
                           '(expression has type "str", variable has type "int")')
        self.assertEqual(expected, problems[1])

    @requires_image('python3')
    def test_process_files_two_files(self):
        self.tool.process_files(self.fixtures)

        self.assertEqual([], self.problems.all(self.fixtures[0]))

        problems = self.problems.all(self.fixtures[1])
        self.assertEqual(3, len(problems))
        expected = Comment(self.fixtures[1], 7, 7, 'Incompatible types in assignment '
                           '(expression has type "List[int]", variable has type "int")')
        self.assertEqual(expected, problems[0])

        expected = Comment(self.fixtures[1], 8, 8, 'Incompatible types in assignment '
                           '(expression has type "str", variable has type "int")')
        self.assertEqual(expected, problems[1])

    @requires_image('python3')
    def test_process_files__missing_config(self):
        options = {
            'config': 'tests/fixtures/mypy/missing.ini'
        }
        self.tool = Mypy(self.problems, options, root_dir)
        self.tool.process_files([self.fixtures[1]])

        problems = self.problems.all()
        assert 1 == len(problems)
        assert 'configuration file' in problems[0].body

    @requires_image('python3')
    def test_process_files__invalid_config(self):
        options = {
            'config': 'tests/fixtures/mypy/invalid.ini'
        }
        self.tool = Mypy(self.problems, options, root_dir)
        self.tool.process_files([self.fixtures[1]])

        problems = self.problems.all()
        assert 3 == len(problems)
