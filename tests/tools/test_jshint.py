from lintreview.review import Problems
from lintreview.review import Comment
from lintreview.tools.jshint import Jshint
from lintreview.utils import in_path
from lintreview.utils import npm_exists
from unittest import TestCase
from unittest import skipIf
from nose.tools import eq_

jshint_missing = not(in_path('jshint') or npm_exists('jshint'))


class TestJshint(TestCase):

    needs_jshint = skipIf(jshint_missing, 'Needs jshint to run')

    fixtures = [
        'tests/fixtures/jshint/no_errors.js',
        'tests/fixtures/jshint/has_errors.js',
        'tests/fixtures/jshint/error_on_multiple_lines.js',
    ]

    def setUp(self):
        self.problems = Problems()
        self.tool = Jshint(self.problems)

    def test_match_file(self):
        self.assertFalse(self.tool.match_file('test.php'))
        self.assertFalse(self.tool.match_file('dir/name/test.py'))
        self.assertFalse(self.tool.match_file('test.py'))
        self.assertTrue(self.tool.match_file('test.js'))
        self.assertTrue(self.tool.match_file('dir/name/test.js'))

    @needs_jshint
    def test_check_dependencies(self):
        self.assertTrue(self.tool.check_dependencies())

    @needs_jshint
    def test_process_files__one_file_pass(self):
        self.tool.process_files([self.fixtures[0]])
        eq_([], self.problems.all(self.fixtures[0]))

    @needs_jshint
    def test_process_files__one_file_fail(self):
        self.tool.process_files([self.fixtures[1]])
        problems = self.problems.all(self.fixtures[1])
        eq_(4, len(problems))

        fname = self.fixtures[1]
        expected = Comment(fname, 1, 1,'Missing name in function declaration.')
        eq_(expected, problems[0])

        expected = Comment(fname, 6, 6, "Use '===' to compare with 'null'.")
        eq_(expected, problems[2])

    @needs_jshint
    def test_process_files__multiple_error(self):
        self.tool.process_files([self.fixtures[2]])
        problems = self.problems.all(self.fixtures[2])
        eq_(6, len(problems))

        fname = self.fixtures[2]
        expected = Comment(fname, 9, 9, "Missing semicolon.")
        eq_(expected, problems[2])

        expected = Comment(fname, 5, 5, "'go' is not defined.")
        eq_(expected, problems[4])

    @needs_jshint
    def test_process_files_two_files(self):
        self.tool.process_files(self.fixtures)

        eq_([], self.problems.all(self.fixtures[0]))

        problems = self.problems.all(self.fixtures[1])
        eq_(4, len(problems))

    @needs_jshint
    def test_process_files_with_config(self):
        config = {
            'config': 'tests/fixtures/jshint/config.json'
        }
        tool = Jshint(self.problems, config)
        tool.process_files([self.fixtures[1]])

        problems = self.problems.all(self.fixtures[1])

        eq_(3, len(problems), 'Config file should lower error count.')

    def test_create_command__with_path_based_standard(self):
        config = {
            'config': 'test/jshint.json'
        }
        tool = Jshint(self.problems, config, '/some/path')
        result = tool.create_command(['some/file.js'])
        expected = [
            '--checkstyle-reporter',
            '--config', '/some/path/test/jshint.json',
            'some/file.js'
        ]
        assert 'jshint' in result[0], 'jshint is in command name'
        eq_(result[1:], expected)
