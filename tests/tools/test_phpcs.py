from lintreview.review import Problems
from lintreview.review import Comment
from lintreview.tools.phpcs import Phpcs
from lintreview.utils import in_path
from unittest import TestCase
from unittest import skipIf
from nose.tools import eq_

phpcs_missing = not(in_path('phpcs'))


class Testphpcs(TestCase):

    fixtures = [
        'tests/fixtures/phpcs/no_errors.php',
        'tests/fixtures/phpcs/has_errors.php',
    ]

    def setUp(self):
        self.problems = Problems()
        self.tool = Phpcs(self.problems)

    def test_match_file(self):
        self.assertTrue(self.tool.match_file('test.php'))
        self.assertTrue(self.tool.match_file('dir/name/test.php'))
        self.assertFalse(self.tool.match_file('dir/name/test.py'))
        self.assertFalse(self.tool.match_file('test.py'))
        self.assertFalse(self.tool.match_file('test.js'))

    @skipIf(phpcs_missing, 'Missing phpcs, cannot run')
    def test_check_dependencies(self):
        self.assertTrue(self.tool.check_dependencies())

    @skipIf(phpcs_missing, 'Missing phpcs, cannot run')
    def test_process_files__one_file_pass(self):
        self.tool.process_files([self.fixtures[0]])
        eq_([], self.problems.all(self.fixtures[0]))

    @skipIf(phpcs_missing, 'Missing phpcs, cannot run')
    def test_process_files__one_file_fail(self):
        self.tool.process_files([self.fixtures[1]])
        problems = self.problems.all(self.fixtures[1])
        eq_(12, len(problems))

        fname = self.fixtures[1]
        expected = Comment(fname, 7, 7, 'PHP version not specified')
        eq_(expected, problems[0])

        expected = Comment(
            fname,
            16,
            16,
            "Line indented incorrectly; expected at least 4 spaces, found 1")
        eq_(expected, problems[11])

    @skipIf(phpcs_missing, 'Missing phpcs, cannot run')
    def test_process_files_two_files(self):
        self.tool.process_files(self.fixtures)

        eq_([], self.problems.all(self.fixtures[0]))

        problems = self.problems.all(self.fixtures[1])
        eq_(12, len(problems))

    @skipIf(phpcs_missing, 'Missing phpcs, cannot run')
    def test_process_files_with_config(self):
        config = {
            'standard': 'Zend'
        }
        tool = Phpcs(self.problems, config)
        tool.process_files([self.fixtures[1]])

        problems = self.problems.all(self.fixtures[1])

        eq_(8, len(problems), 'Changing standards changes error counts')

    def test_create_command__with_path_based_standard(self):
        config = {
            'standard': 'test/CodeStandards'
        }
        tool = Phpcs(self.problems, config, '/some/path')
        result = tool.create_command(['some/file.php'])
        expected = [
            'phpcs',
            '--report=checkstyle',
            '--standard=/some/path/test/CodeStandards',
            '--extensions=php',
            'some/file.php'
        ]
        eq_(result, expected)
