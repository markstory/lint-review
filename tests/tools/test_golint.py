from __future__ import absolute_import
from lintreview.review import Problems, Comment
from lintreview.tools.golint import Golint
from unittest import TestCase
from mock import patch
from tests import root_dir, read_file, read_and_restore_file, requires_image


class TestGolint(TestCase):

    fixtures = [
        'tests/fixtures/golint/no_errors.go',
        'tests/fixtures/golint/has_errors.go',
        'tests/fixtures/golint/http.go',
    ]

    def setUp(self):
        self.problems = Problems()
        self.tool = Golint(self.problems, {}, root_dir)

    def test_match_file(self):
        self.assertTrue(self.tool.match_file('test.go'))
        self.assertTrue(self.tool.match_file('dir/name/test.go'))
        self.assertFalse(self.tool.match_file('dir/name/test.py'))
        self.assertFalse(self.tool.match_file('test.php'))
        self.assertFalse(self.tool.match_file('test.golp'))

    @requires_image('golint')
    def test_check_dependencies(self):
        self.assertTrue(self.tool.check_dependencies())

    @requires_image('golint')
    def test_process_files__one_file_pass(self):
        self.tool.process_files([self.fixtures[0]])
        self.assertEqual([], self.problems.all(self.fixtures[0]))

    @requires_image('golint')
    def test_process_files__one_file_fail(self):
        self.tool.process_files([self.fixtures[1]])
        problems = self.problems.all(self.fixtures[1])
        self.assertEqual(2, len(problems))

        fname = self.fixtures[1]
        expected = Comment(
            fname,
            9,
            9,
            'exported function Foo should have comment or be unexported')
        self.assertEqual(expected, problems[0])

        expected = Comment(
            fname,
            14,
            14,
            "if block ends with a return statement, "
            "so drop this else and outdent its block")
        self.assertEqual(expected, problems[1])

    @requires_image('golint')
    def test_process_files_two_files(self):
        self.tool.process_files([self.fixtures[0], self.fixtures[1]])

        self.assertEqual([], self.problems.all(self.fixtures[0]))

        problems = self.problems.all(self.fixtures[1])
        self.assertEqual(2, len(problems))

    @requires_image('golint')
    def test_process_files_in_different_packages(self):
        self.tool.process_files([self.fixtures[1], self.fixtures[2]])

        problems = self.problems.all()
        self.assertEqual(3, len(problems))
        self.assertEqual(2, len(self.problems.all(self.fixtures[1])))
        self.assertEqual(1, len(self.problems.all(self.fixtures[2])))

    @requires_image('golint')
    @patch('lintreview.docker.run')
    def test_process_files_with_config__mocked(self, mock_command):
        mock_command.return_value = ""
        config = {
            'min_confidence': 0.95
        }
        tool = Golint(self.problems, config, root_dir)
        tool.process_files([self.fixtures[1]])

        mock_command.assert_called_with(
            'golint',
            [
                'golint', '-min_confidence', 0.95, self.fixtures[1]
            ],
            root_dir)

    @requires_image('golint')
    def test_process_files_with_config(self):
        config = {
            'min_confidence': 0.95
        }
        tool = Golint(self.problems, config, root_dir)
        tool.process_files([self.fixtures[1]])
        self.assertEqual(2, len(self.problems))

    @requires_image('golint')
    def test_process_files_with_ignores(self):
        config = {
            'min_confidence': 0.3,
            'ignore': [
                r'exported function \w+ should have comment',
                r'has_errors\.go'
            ]
        }
        tool = Golint(self.problems, config, root_dir)
        tool.process_files([self.fixtures[1]])
        self.assertEqual(0, len(self.problems))

    @requires_image('golint')
    def test_process_files_with_invalid_ignore_pattern(self):
        config = {
            'min_confidence': 0.3,
            'ignore': [
                '(.*',
            ]
        }
        tool = Golint(self.problems, config, root_dir)
        tool.process_files([self.fixtures[1]])
        problems = self.problems.all()
        self.assertIn('Invalid golint ignore rule `(.*`', problems[0].body)
        self.assertIn('exported function', problems[1].body)

    def test_has_fixer__not_enabled(self):
        tool = Golint(self.problems, {})
        self.assertEqual(False, tool.has_fixer())

    def test_has_fixer__enabled(self):
        tool = Golint(self.problems, {'fixer': True})
        self.assertEqual(True, tool.has_fixer())

    @requires_image('golint')
    def test_execute_fixer(self):
        tool = Golint(self.problems, {'fixer': True}, root_dir)

        original = read_file(self.fixtures[1])
        tool.execute_fixer(self.fixtures)

        updated = read_and_restore_file(self.fixtures[1], original)
        assert original != updated, 'File content should change.'
        self.assertEqual(0, len(self.problems.all()),
                         'No errors should be recorded')
