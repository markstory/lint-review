from lintreview.review import Problems, Comment
from lintreview.tools.jshint import Jshint
from unittest import TestCase
from tests import root_dir, requires_image


class TestJshint(TestCase):

    fixtures = [
        'tests/fixtures/jshint/no_errors.js',
        'tests/fixtures/jshint/has_errors.js',
        'tests/fixtures/jshint/error_on_multiple_lines.js',
    ]

    def setUp(self):
        self.problems = Problems()
        self.tool = Jshint(self.problems, base_path=root_dir)

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
    def test_process_files__one_file_pass(self):
        self.tool.process_files([self.fixtures[0]])
        self.assertEqual([], self.problems.all(self.fixtures[0]))

    @requires_image('nodejs')
    def test_process_files__one_file_fail(self):
        self.tool.process_files([self.fixtures[1]])
        problems = self.problems.all(self.fixtures[1])
        self.assertEqual(3, len(problems))

        fname = self.fixtures[1]
        expected = Comment(fname, 1, 1,
                           'Missing name in function declaration.')
        self.assertEqual(expected, problems[0])

        expected = Comment(fname, 4, 4, "Missing semicolon.")
        self.assertEqual(expected, problems[1])

    @requires_image('nodejs')
    def test_process_files__multiple_error(self):
        self.tool.process_files([self.fixtures[2]])
        problems = self.problems.all(self.fixtures[2])
        self.assertEqual(6, len(problems))

        fname = self.fixtures[2]
        expected = Comment(fname, 9, 9, "Missing semicolon.")
        self.assertEqual(expected, problems[2])

        expected = Comment(fname, 5, 5, "'go' is not defined.")
        self.assertEqual(expected, problems[4])

    @requires_image('nodejs')
    def test_process_files_two_files(self):
        self.tool.process_files(self.fixtures)

        self.assertEqual([], self.problems.all(self.fixtures[0]))

        problems = self.problems.all(self.fixtures[1])
        self.assertEqual(3, len(problems))

    @requires_image('nodejs')
    def test_process_files_with_config(self):
        config = {
            'config': 'tests/fixtures/jshint/config.json'
        }
        tool = Jshint(self.problems, config, root_dir)
        tool.process_files([self.fixtures[1]])

        problems = self.problems.all(self.fixtures[1])

        self.assertEqual(3, len(problems),
                         'Config file should lower error count.')

    def test_create_command__with_path_based_standard(self):
        config = {
            'config': 'test/jshint.json'
        }
        tool = Jshint(self.problems, config, root_dir)
        result = tool.create_command(['some/file.js'])
        expected = [
            '--checkstyle-reporter',
            '--config', '/src/test/jshint.json',
            'some/file.js'
        ]
        assert 'jshint' in result[0], 'jshint is in command name'
        self.assertEqual(result[1:], expected)
