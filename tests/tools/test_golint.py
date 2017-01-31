from lintreview.review import Problems, Comment
from lintreview.tools.golint import Golint
from lintreview.utils import go_bin_path
from unittest import TestCase, skipIf
from nose.tools import eq_
from mock import patch

golint_missing = not(go_bin_path('golint'))


class TestGolint(TestCase):

    needs_golint = skipIf(golint_missing, 'Needs phpcs')

    fixtures = [
        'tests/fixtures/golint/no_errors.go',
        'tests/fixtures/golint/has_errors.go',
        'tests/fixtures/golint/http.go',
    ]

    def setUp(self):
        self.problems = Problems()
        self.tool = Golint(self.problems)

    def test_match_file(self):
        self.assertTrue(self.tool.match_file('test.go'))
        self.assertTrue(self.tool.match_file('dir/name/test.go'))
        self.assertFalse(self.tool.match_file('dir/name/test.py'))
        self.assertFalse(self.tool.match_file('test.php'))
        self.assertFalse(self.tool.match_file('test.golp'))

    @needs_golint
    def test_check_dependencies(self):
        self.assertTrue(self.tool.check_dependencies())

    @needs_golint
    def test_process_files__one_file_pass(self):
        self.tool.process_files([self.fixtures[0]])
        eq_([], self.problems.all(self.fixtures[0]))

    @needs_golint
    def test_process_files__one_file_fail(self):
        self.tool.process_files([self.fixtures[1]])
        problems = self.problems.all(self.fixtures[1])
        eq_(2, len(problems))

        fname = self.fixtures[1]
        expected = Comment(
            fname,
            9,
            9,
            'exported function Foo should have comment or be unexported')
        eq_(expected, problems[0])

        expected = Comment(
            fname,
            14,
            14,
            "if block ends with a return statement, "
            "so drop this else and outdent its block")
        eq_(expected, problems[1])

    @needs_golint
    def test_process_files_two_files(self):
        self.tool.process_files([self.fixtures[0], self.fixtures[1]])

        eq_([], self.problems.all(self.fixtures[0]))

        problems = self.problems.all(self.fixtures[1])
        eq_(2, len(problems))

    @needs_golint
    def test_process_files_in_different_packages(self):
        self.tool.process_files([self.fixtures[1], self.fixtures[2]])

        problems = self.problems.all()
        eq_(3, len(problems))
        eq_(2, len(self.problems.all(self.fixtures[1])))
        eq_(1, len(self.problems.all(self.fixtures[2])))

    @needs_golint
    @patch('lintreview.tools.golint.run_command')
    def test_process_files_with_config__mocked(self, mock_command):
        mock_command.return_value = []
        config = {
            'min_confidence': 0.95
        }
        tool = Golint(self.problems, config)
        tool.process_files([self.fixtures[1]])

        mock_command.assert_called_with(
            [
                go_bin_path('golint'),
                '-min_confidence', 0.95,
                self.fixtures[1]
            ],
            ignore_error=True,
            split=True)

    @needs_golint
    def test_process_files_with_config(self):
        config = {
            'min_confidence': 0.95
        }
        tool = Golint(self.problems, config)
        tool.process_files([self.fixtures[1]])
        eq_(2, len(self.problems))
